from entity import Agent


def main() -> None:
    agent = Agent({"server": {"host": "127.0.0.1", "port": 8000}})
    agent.run()


if __name__ == "__main__":
    main()
