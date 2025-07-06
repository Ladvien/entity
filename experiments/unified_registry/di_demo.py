"""Demonstrates using AsyncResourceManager with different DI frameworks."""

from __future__ import annotations

from fastapi import Depends, FastAPI

from experiments.unified_registry.resource_manager import (
    AsyncResourceManager,
    BaseResource,
)

app = FastAPI()
manager = AsyncResourceManager()


def get_resource(name: str) -> BaseResource:
    resource = manager.get(name)
    if resource is None:
        raise RuntimeError(f"Resource '{name}' not registered")
    return resource


@app.on_event("startup")
async def startup_event() -> None:
    await manager.initialize_all()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await manager.shutdown_all()


@app.get("/health")
async def health() -> dict[str, bool]:
    return await manager.health_report()


# Dependency example using FastAPI's Depends
@app.get("/items/{item_id}")
async def read_item(
    item_id: int,
    db: BaseResource = Depends(lambda: get_resource("db")),
) -> dict[str, int]:
    return {"item_id": item_id}


# Django integration would typically use the manager in middleware or apps.py.
# For brevity this example focuses on FastAPI.
