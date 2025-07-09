from __future__ import annotations

import pytest
from entity.core.validation.input import validate_params
from pydantic import BaseModel


class Echo:
    class Params(BaseModel):
        text: str

    @validate_params(Params)
    async def run(self, params: Params) -> str:
        return params.text


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_params_accepts_model_instance() -> None:
    obj = Echo()
    model = Echo.Params(text="hi")
    assert await obj.run(model) == "hi"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_params_validates_dict() -> None:
    obj = Echo()
    assert await obj.run({"text": "hello"}) == "hello"
