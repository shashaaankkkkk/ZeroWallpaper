"""Configuration management for ZeroWallpaper."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


def _get_app_dir() -> Path:
    """Get the application data directory."""
    app_dir = Path.home() / ".zerowallpaper"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


@dataclass
class AutoChangeConfig:
    """Auto-change feature configuration."""
    enabled: bool = False
    interval_minutes: int = 30
    tags: list[str] = field(default_factory=list)


@dataclass
class UIConfig:
    """UI configuration."""
    theme: str = "dark"
    preview_quality: str = "medium"


@dataclass
class AppConfig:
    """Application configuration."""
    github_token: str = ""
    cache_ttl_hours: int = 24
    auto_change: AutoChangeConfig = field(default_factory=AutoChangeConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    @classmethod
    def load(cls) -> "AppConfig":
        """Load configuration from disk, creating defaults if needed."""
        config_path = _get_app_dir() / "config.json"

        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                return cls._from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # Create default config
        config = cls()
        config.save()
        return config

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        """Create config from dictionary."""
        auto_change_data = data.get("auto_change", {})
        ui_data = data.get("ui", {})

        return cls(
            github_token=data.get("github_token", ""),
            cache_ttl_hours=data.get("cache_ttl_hours", 24),
            auto_change=AutoChangeConfig(
                enabled=auto_change_data.get("enabled", False),
                interval_minutes=auto_change_data.get("interval_minutes", 30),
                tags=auto_change_data.get("tags", []),
            ),
            ui=UIConfig(
                theme=ui_data.get("theme", "dark"),
                preview_quality=ui_data.get("preview_quality", "medium"),
            ),
        )

    def save(self) -> None:
        """Save configuration to disk."""
        config_path = _get_app_dir() / "config.json"
        config_path.write_text(json.dumps(asdict(self), indent=2))

    @property
    def app_dir(self) -> Path:
        """Get app data directory."""
        return _get_app_dir()

    @property
    def cache_dir(self) -> Path:
        """Get cache directory."""
        d = self.app_dir / "cache"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def thumbnails_dir(self) -> Path:
        """Get thumbnails directory."""
        d = self.cache_dir / "thumbnails"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def wallpapers_dir(self) -> Path:
        """Get wallpapers directory."""
        d = self.cache_dir / "wallpapers"
        d.mkdir(parents=True, exist_ok=True)
        return d
