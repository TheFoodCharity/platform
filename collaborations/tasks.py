import io
import logging
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

import clamd
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile, File
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError

from .models import CollaborationFile, collaboration_clean_file_path

logger = logging.getLogger(__name__)

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = 89478485

COMPRESSIBLE_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}
IMAGE_COMPRESSION_ERRORS = (OSError, UnidentifiedImageError)
MAX_COMPRESSED_IMAGE_SIZE = (1920, 1080)
JPEG_COMPRESSION_QUALITY = 80


@dataclass(frozen=True)
class StoredFile:
    name: str
    size: int


class ScanTaskResult(str, Enum):
    SKIPPED = "skipped"
    CLEAN = "clean"
    INFECTED = "infected"
    FAILED = "failed"


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def scan_collaboration_file(self, collaboration_file_id: str) -> str:
    collaboration_file = _claim_file_for_scan(collaboration_file_id)
    if not collaboration_file:
        logger.info("File ID %s skipped: not found or not in pending/failed state.", collaboration_file_id)
        return ScanTaskResult.SKIPPED.value

    logger.info("Initiating ClamAV scan for file ID: %s", collaboration_file_id)

    try:
        status, reason = _scan_file_with_clamav(collaboration_file)

    except clamd.BufferTooLongError as exc:
        logger.exception("File ID %s exceeded ClamAV stream size limit.", collaboration_file_id)
        _mark_scan_failed(collaboration_file.id, "ClamAV stream size limit exceeded.", exc)
        return ScanTaskResult.FAILED.value

    except clamd.ConnectionError as exc:
        logger.warning("ClamAV connection error scanning file ID %s. Retrying...", collaboration_file_id)
        return _retry_or_fail(self, collaboration_file.id, exc)

    except (FileNotFoundError, clamd.ResponseError) as exc:
        logger.exception("ClamAV failed to scan file ID %s.", collaboration_file_id)
        _mark_scan_failed(collaboration_file.id, "ClamAV could not scan the file.", exc)
        return ScanTaskResult.FAILED.value

    except OSError as exc:
        logger.warning("OS error scanning file ID %s. Retrying...", collaboration_file_id)
        return _retry_or_fail(self, collaboration_file.id, exc)

    if status == "OK":
        logger.info("File ID %s is clean. Moving to safe storage.", collaboration_file_id)
        return _handle_clean_scan(self, collaboration_file)

    if status == "FOUND":
        logger.warning("Malware found in file ID %s! Reason: %s", collaboration_file_id, reason)
        _mark_scan_infected(collaboration_file, reason)
        return ScanTaskResult.INFECTED.value

    logger.error("Unexpected ClamAV status '%s' for file ID %s", status, collaboration_file_id)
    _mark_scan_failed(
        collaboration_file.id,
        f"ClamAV returned an unexpected scan status: {status}",
        reason,
    )
    return ScanTaskResult.FAILED.value


def _handle_clean_scan(task, collaboration_file: CollaborationFile) -> str:
    try:
        _mark_scan_clean(collaboration_file)
    except OSError as exc:
        logger.warning("OS Error promoting clean file ID %s. Retrying...", collaboration_file.id)
        return _retry_or_fail(task, collaboration_file.id, exc)
    except Exception as exc:
        logger.exception("Failed to promote clean file ID %s from quarantine.", collaboration_file.id)
        _mark_scan_failed(collaboration_file.id, "Could not promote clean file from quarantine.", exc)
        return ScanTaskResult.FAILED.value

    return ScanTaskResult.CLEAN.value


def _claim_file_for_scan(collaboration_file_id: str | UUID) -> CollaborationFile | None:
    with transaction.atomic():
        try:
            collaboration_file = CollaborationFile.objects.select_for_update().get(pk=collaboration_file_id)
        except CollaborationFile.DoesNotExist:
            return None

        if collaboration_file.scan_status not in [
            CollaborationFile.ScanStatus.PENDING,
            CollaborationFile.ScanStatus.FAILED,
        ]:
            return None

        collaboration_file.scan_status = CollaborationFile.ScanStatus.SCANNING
        collaboration_file.scan_result = ""
        collaboration_file.scan_error = ""
        collaboration_file.scan_started_at = timezone.now()
        collaboration_file.scan_attempts += 1
        collaboration_file.save(
            update_fields=[
                "scan_status",
                "scan_result",
                "scan_error",
                "scan_started_at",
                "scan_attempts",
            ]
        )
        return collaboration_file


def _scan_file_with_clamav(collaboration_file: CollaborationFile) -> tuple[str, str]:
    scanner = clamd.ClamdNetworkSocket(
        host=settings.CLAMAV_HOST,
        port=settings.CLAMAV_PORT,
        timeout=settings.CLAMAV_TIMEOUT,
    )

    with collaboration_file.file.open("rb") as uploaded_file:
        scan_result = scanner.instream(uploaded_file)
    return _parse_clamav_result(scan_result)


def _parse_clamav_result(scan_result: dict) -> tuple[str, str]:
    if not scan_result:
        raise clamd.ResponseError("ClamAV returned an empty scan result.")

    status, reason = next(iter(scan_result.values()))
    return status, reason or ""


def _mark_scan_clean(collaboration_file: CollaborationFile) -> None:
    old_name = collaboration_file.file.name

    stored_file = _copy_file_to_clean_storage(collaboration_file)

    CollaborationFile.objects.filter(pk=collaboration_file.pk).update(
        file=stored_file.name,
        size=stored_file.size,
        scan_status=CollaborationFile.ScanStatus.CLEAN,
        scan_result="OK",
        scan_error="",
        scanned_at=timezone.now(),
    )

    delete_error = _delete_storage_file(collaboration_file.file.storage, old_name)
    if delete_error:
        logger.error(
            "Clean file ID %s promoted, but quarantine cleanup failed for %s: %s",
            collaboration_file.id,
            old_name,
            delete_error,
        )


def _copy_file_to_clean_storage(collaboration_file: CollaborationFile) -> StoredFile:
    storage = collaboration_file.file.storage
    old_name = collaboration_file.file.name
    new_name = collaboration_clean_file_path(collaboration_file)

    if storage.exists(new_name):
        storage.delete(new_name)

    with storage.open(old_name, "rb") as source:
        content = _prepare_clean_file_content(collaboration_file, source)
        saved_name = storage.save(new_name, content)

    return StoredFile(name=saved_name, size=storage.size(saved_name))


def _prepare_clean_file_content(collaboration_file: CollaborationFile, source) -> File:
    if collaboration_file.content_type not in COMPRESSIBLE_IMAGE_CONTENT_TYPES:
        return File(source)

    compressed_content = _compress_image_content(source, collaboration_file.content_type)
    if compressed_content:
        return compressed_content

    source.seek(0)
    return File(source)


def _compress_image_content(source, content_type: str) -> ContentFile | None:
    try:
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail(MAX_COMPRESSED_IMAGE_SIZE, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            if content_type == "image/jpeg":
                image = _prepare_jpeg_image(image)
                image.save(
                    output,
                    format="JPEG",
                    quality=JPEG_COMPRESSION_QUALITY,
                    optimize=True,
                    progressive=True,
                )
            elif content_type == "image/png":
                image.save(output, format="PNG", optimize=True)
            else:
                return None
    except IMAGE_COMPRESSION_ERRORS:
        logger.exception("Could not compress image; retaining the scanned original file.")
        return None

    return ContentFile(output.getvalue())


def _prepare_jpeg_image(image: Image.Image) -> Image.Image:
    if image.mode in ("RGB", "L"):
        return image
    return image.convert("RGB")


def _mark_scan_infected(collaboration_file: CollaborationFile, reason: str) -> None:
    delete_error = _delete_storage_file(collaboration_file.file.storage, collaboration_file.file.name)
    scan_error = f"Could not delete infected file from storage: {delete_error}" if delete_error else ""

    if delete_error:
        logger.error("Failed to delete infected file ID %s from storage: %s", collaboration_file.id, delete_error)
    else:
        logger.info("Successfully deleted infected file ID %s from storage.", collaboration_file.id)

    CollaborationFile.objects.filter(pk=collaboration_file.pk).update(
        scan_status=CollaborationFile.ScanStatus.INFECTED,
        scan_result=_truncate(reason or "FOUND", CollaborationFile._meta.get_field("scan_result").max_length),
        scan_error=scan_error,
        scanned_at=timezone.now(),
    )


def _retry_or_fail(task, collaboration_file_id: str | UUID, exc: Exception) -> str:
    if task.request.retries < task.max_retries:
        logger.info(
            "Retrying task for file ID %s (Attempt %d/%d)",
            collaboration_file_id,
            task.request.retries + 1,
            task.max_retries,
        )
        _mark_scan_pending_retry(collaboration_file_id, exc)
        raise task.retry(exc=exc)

    logger.error("ClamAV scan failed for file ID %s after all retries.", collaboration_file_id)
    _mark_scan_failed(collaboration_file_id, "ClamAV scan failed after all retry attempts.", exc)
    return ScanTaskResult.FAILED.value


def _mark_scan_pending_retry(collaboration_file_id: str | UUID, exc: Exception) -> None:
    CollaborationFile.objects.filter(pk=collaboration_file_id).update(
        scan_status=CollaborationFile.ScanStatus.PENDING,
        scan_error=_truncate(str(exc), CollaborationFile._meta.get_field("scan_error").max_length),
    )


def _mark_scan_failed(collaboration_file_id: str | UUID, message: str, details: Exception | None = None) -> None:
    detail_text = str(details) if details else ""
    error = message if not detail_text else f"{message} {detail_text}"
    CollaborationFile.objects.filter(pk=collaboration_file_id).update(
        scan_status=CollaborationFile.ScanStatus.FAILED,
        scan_error=error,
        scanned_at=timezone.now(),
    )


def _delete_storage_file(storage, name: str) -> str:
    if not name:
        return ""

    try:
        storage.delete(name)
    except Exception as exc:
        return str(exc)
    return ""


def _truncate(value: str, max_length: int | None) -> str:
    if max_length is None or len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."
