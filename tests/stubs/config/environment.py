from pathlib import Path

from dotenv import load_dotenv


def load_env(env_file: str | Path = ".env") -> None:
    env_path = Path(env_file)
    if env_path.exists():
        load_dotenv(env_path)
