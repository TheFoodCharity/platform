from abc import ABC, abstractmethod
from enum import StrEnum, auto
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, SecretStr, model_validator
from pydantic.networks import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _split_comma_list(v: object) -> object:
    if isinstance(v, str):
        return [item.strip() for item in v.split(",")]
    return v


def _blank_to_none(v: object) -> object:
    if isinstance(v, str) and not v.strip():
        return None
    return v


CommaSeparatedList = Annotated[list[str], NoDecode, BeforeValidator(_split_comma_list)]


class DatabaseUrl(PostgresDsn):
    @model_validator(mode="after")
    def has_database_name(self):
        if (name := self.path) is None or len(name) <= 1:
            raise ValueError("missing database name")
        return self

    @model_validator(mode="after")
    def only_one_host(self):
        try:
            [_database] = self.hosts()
        except ValueError:
            raise ValueError("exactly one host must be provided") from None
        return self

    def to_django(self) -> dict:
        [database] = self.hosts()
        options = {key.upper(): value for key, value in database.items()}

        if (username := options.pop("USERNAME", None)) is not None:
            options["USER"] = username

        name = self.path
        assert name is not None
        options["NAME"] = name.removeprefix("/")

        return options


class SmtpSecurity(StrEnum):
    STARTTLS = auto()
    SMTPS = auto()
    NONE = auto()


class SmtpSettings(BaseModel):
    model_config = ConfigDict(validate_default=True)

    from_email: str = Field(default="no-reply@fcacp.local")

    host: str = Field(default="127.0.0.1")
    port: int = Field(default=1025)
    username: str = Field(default="fcacp")
    password: SecretStr = Field(default="super-secure-password")
    security: SmtpSecurity = Field(default=SmtpSecurity.NONE)
    timeout: int | None = Field(default=None)

    @property
    def use_tls(self) -> bool:
        return self.security == SmtpSecurity.STARTTLS

    @property
    def use_ssl(self) -> bool:
        return self.security == SmtpSecurity.SMTPS


class ClamAVSettings(BaseModel):
    model_config = ConfigDict(validate_default=True)

    host: str = Field(default="127.0.0.1")
    port: int = Field(default=3310)
    timeout: int = Field(default=60)


class BaseStorage(ABC):
    @abstractmethod
    def to_django(self) -> dict: ...


class LocalStorage(BaseStorage, BaseModel):
    model_config = ConfigDict(validate_default=True)

    type: Literal["local"] = "local"
    path: Path = "./private_media"

    def to_django(self) -> dict:
        return {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {
                "location": self.path.resolve(),
            },
        }


class S3Protocol(StrEnum):
    HTTP = auto()
    HTTPS = auto()


class S3Storage(BaseStorage, BaseModel):
    type: Literal["s3"] = "s3"
    bucket: str
    region: str | None = None
    access_key_id: str | None = None
    secret_access_key: str | None = None

    protocol: S3Protocol = S3Protocol.HTTPS
    endpoint: str | None = None

    def to_django(self) -> dict:
        endpoint_url = None
        if (endpoint := self.endpoint) is not None:
            if endpoint.startswith("http") or endpoint.startswith("https"):
                endpoint_url = endpoint
            else:
                endpoint_url = f"{self.protocol.value}://{endpoint}"

        return {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": self.bucket,
                "region_name": self.region,
                "access_key": self.access_key_id,
                "secret_key": self.secret_access_key,
                "endpoint_url": endpoint_url,
                "default_acl": None,
                "querystring_auth": True,
                "file_overwrite": False,
            },
        }


class BaseEnvironment(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    allowed_hosts: CommaSeparatedList = []
    database_url: DatabaseUrl = Field(default="postgresql://fcacp:super-secure-password@127.0.0.1:5432/fcacp")
    broker_url: RedisDsn = Field(default="redis://127.0.0.1:6379/0")

    smtp: SmtpSettings = SmtpSettings()
    clamav: ClamAVSettings = ClamAVSettings()
    storage: LocalStorage | S3Storage = Field(discriminator="type", default_factory=LocalStorage)


class DevelopmentEnvironment(BaseEnvironment):
    secret_key: Annotated[SecretStr | None, BeforeValidator(_blank_to_none)] = None


class ProductionEnvironment(BaseEnvironment):
    secret_key: Annotated[SecretStr, BeforeValidator(_blank_to_none)]

    https: bool = True
