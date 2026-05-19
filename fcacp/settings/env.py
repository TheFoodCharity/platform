from enum import StrEnum, auto
from typing import Annotated

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

    aws_storage_bucket_name: str = ""
    aws_s3_region_name: str = ""
    aws_s3_access_key_id: str = ""
    aws_s3_secret_access_key: str = ""


class DevelopmentEnvironment(BaseEnvironment):
    secret_key: Annotated[SecretStr | None, BeforeValidator(_blank_to_none)] = None


class ProductionEnvironment(BaseEnvironment):
    secret_key: Annotated[SecretStr, BeforeValidator(_blank_to_none)]

    https: bool = True
