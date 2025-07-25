from __future__ import annotations

"""Run a minimal agent with Docker services.

Start the dependencies before running this script:

```
docker compose up -d
```
"""

import asyncio

from entity import Agent


async def main() -> None:
    agent = Agent()
    await agent.chat("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
