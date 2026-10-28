"""Server settings, read from PIC2COOKIE_* environment variables or a .env file.

Nested settings use a double underscore, e.g. PIC2COOKIE_STORAGE__TYPE=s3.
"""

from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseModel):
    type: Literal["fs", "s3"] = "fs"
    path: Path = Path("data")  # fs: a local folder or a mounted volume
    bucket: str | None = None  # s3
    prefix: str = ""
    endpoint_url: str | None = None  # for MinIO, Garage, ...
    region: str | None = None
    access_key_id: str | None = None  # falls back to the usual AWS_* variables
    secret_access_key: str | None = None


class DatabaseSettings(BaseModel):
    uri: str | None = None  # set to store Design records in MongoDB
    name: str = "pic2cookie"


class RetentionSettings(BaseModel):
    days: int | None = None  # delete Designs not changed for this long


class LimitSettings(BaseModel):
    upload_mb: float = 10
    max_pixels: int = 4096  # longest side of an uploaded raster picture
    job_timeout: int = 120  # seconds


class LogSettings(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["text", "json"] = "text"  # json: one JSON object per line, for Loki & co.
    access: bool = True  # log every request (with the visitor's IP address)


class OperatorSettings(BaseModel):
    """Who runs a hosted instance; named in the privacy notice (Art. 13 GDPR)."""

    name: str | None = None
    address: str | None = None
    email: str | None = None


class HostingSettings(BaseModel):
    """Running as a service for others: shows the source link and a privacy notice."""

    enabled: bool = False
    repository_url: str = "https://github.com/LevinTheDoctor/pic2cookie"
    operator: OperatorSettings = OperatorSettings()
    privacy_url: str | None = None  # link to your own full privacy policy as well


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PIC2COOKIE_", env_nested_delimiter="__", env_file=".env", extra="ignore"
    )

    storage: StorageSettings = StorageSettings()
    database: DatabaseSettings = DatabaseSettings()
    executor: Literal["inline", "rq"] = "inline"
    redis_url: str = "redis://localhost:6379/0"
    retention: RetentionSettings = RetentionSettings()
    limits: LimitSettings = LimitSettings()
    hosting: HostingSettings = HostingSettings()
    log: LogSettings = LogSettings()
    frontend_dir: Path | None = None  # defaults to frontend/dist next to the package


@cache
def settings() -> Settings:
    return Settings()
