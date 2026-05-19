from enum import StrEnum, auto
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator
from pydantic.networks import PostgresDsn
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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


class Environment(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__")

    debug: bool = False
    secret_key: SecretStr

    allowed_hosts: Annotated[list[str], NoDecode] = []

    database_url: DatabaseUrl = Field(default="postgresql://fcacp:super-secure-password@127.0.0.1:5432/fcacp")

    smtp: SmtpSettings = SmtpSettings()

    aws_storage_bucket_name: str = ""
    aws_s3_region_name: str = ""
    aws_s3_access_key_id: str = ""
    aws_s3_secret_access_key: str = ""

    celery_broker_url: str = "redis://127.0.0.1:6379/0"

    clamav_host: str = "127.0.0.1"
    clamav_port: int = 3310
    clamav_timeout: int = 60

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def decode_allowed_hosts(cls, v: str) -> list[str]:
        return [i.strip() for i in v.split(",")]
