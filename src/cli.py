import argparse

from agent import Agent


class CLI:
    """Command line interface for running an Entity agent."""

    def __init__(self) -> None:
        self.args = self._parse_args()

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Run an Entity agent using a YAML configuration.",
        )
        parser.add_argument(
            "--config",
            "-c",
            required=True,
            help="Path to a YAML configuration file.",
        )
        return parser.parse_args()

    def run(self) -> None:
        agent = Agent(self.args.config)
        agent.run()


def main() -> None:
    CLI().run()


if __name__ == "__main__":
    main()
