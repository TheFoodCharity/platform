from pydantic import Field, model_validator
from pydantic.networks import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class Environment(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__")

    database_url: DatabaseUrl = Field(default="postgresql://fcacp:super-secure-password@127.0.0.1:5432/fcacp")

    aws_storage_bucket_name: str = ""
    aws_s3_region_name: str = ""
    aws_s3_access_key_id: str = ""
    aws_s3_secret_access_key: str = ""

    celery_broker_url: str = "redis://127.0.0.1:6379/0"

    clamav_host: str = "127.0.0.1"
    clamav_port: int = 3310
    clamav_timeout: int = 60
