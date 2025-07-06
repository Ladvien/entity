from __future__ import annotations

import os
from pathlib import Path

from .loader import EnvSecretsProvider, SecureConfigLoader


def main() -> None:
    provider = EnvSecretsProvider()
    loader = SecureConfigLoader(provider)
    enc_file = Path(__file__).with_name("config.yaml.enc")
    config = loader.load(enc_file)
    print(config)


if __name__ == "__main__":  # pragma: no cover - demo
    if "CONFIG_KEY" not in os.environ:
        raise SystemExit("Set CONFIG_KEY environment variable")
    main()
