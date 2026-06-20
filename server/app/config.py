from pathlib import Path
import tomllib

CONFIG_PATH = Path(__file__).parent / "config" / "config.toml"

with open(CONFIG_PATH, "rb") as f:
    CONFIG = tomllib.load(f)
