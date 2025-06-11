def _load_version():
    """Return package version from metadata or setup.cfg."""
    try:
        from importlib.metadata import version

        return version("punch")
    except Exception:
        import configparser
        from pathlib import Path

        config = configparser.ConfigParser()
        cfg_path = Path(__file__).resolve().parent.parent / "setup.cfg"
        if cfg_path.exists():
            config.read(cfg_path)
            return config.get("metadata", "version", fallback="0.0.0")
        return "0.0.0"


__version__ = _load_version()
