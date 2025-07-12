import pytest
from pipeline.initializer import SystemInitializer
from entity.core.plugins import InfrastructurePlugin, ValidationResult
from pipeline.reliability import CircuitBreaker
from pipeline.exceptions import CircuitBreakerTripped, InitializationError


class FailingInfra(InfrastructurePlugin):
    infrastructure_type = "database"
    resource_category = "database"
    stages: list = []
    dependencies: list[str] = []

    async def validate_runtime(
        self, breaker: CircuitBreaker | None = None
    ) -> ValidationResult:
        async def _fail() -> None:
            raise RuntimeError("boom")

        brk = breaker or CircuitBreaker(failure_threshold=1)
        try:
            await brk.call(_fail)
        except Exception as exc:
            if isinstance(exc, CircuitBreakerTripped):
                return ValidationResult.error_result("circuit breaker open")
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()


@pytest.mark.asyncio
async def test_shared_breaker_across_resources():
    cfg = {
        "plugins": {
            "infrastructure": {
                "db1": {"type": f"{__name__}:FailingInfra"},
                "db2": {"type": f"{__name__}:FailingInfra"},
            }
        },
        "workflow": {},
        "runtime_validation_breaker": {"failure_threshold": 5, "database": 2},
    }
    init = SystemInitializer(cfg)
    with pytest.raises(InitializationError):
        await init.initialize()
