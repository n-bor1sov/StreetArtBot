from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: directory that contains the `bot` package (parent of `bot/`).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    mongo_url: str = Field(
        ...,
        description="mongodb:// or mongodb+srv:// URI; DB name from path unless mongo_db_name is set.",
    )
    mongo_db_name: str | None = Field(
        default=None,
        description="Override database name when URI has no path or you want another DB.",
    )
    admin_ids: list[int]
    log_level: str = "INFO"
    assets_dir: Path = Path("assets")

    @field_validator("assets_dir", mode="after")
    @classmethod
    def resolve_assets_dir(cls, v: Path) -> Path:
        """Anchor relative paths to project root so assets resolve under systemd/docker."""
        p = v.expanduser()
        if not p.is_absolute():
            return (_PROJECT_ROOT / p).resolve()
        return p.resolve()

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: object) -> object:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @property
    def photos_dir(self) -> Path:
        return self.assets_dir / "Photos"

    @property
    def scrins_dir(self) -> Path:
        return self.assets_dir / "Scrins"


settings = Settings()
