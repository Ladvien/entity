from entity.core.compatibility import (
    register_compatibility,
    is_upgrade_supported,
)


def test_upgrade_matrix() -> None:
    register_compatibility("0.0.1", ["0.0.2"])
    register_compatibility("0.0.2", ["0.1.0"])
    assert is_upgrade_supported("0.0.1", "0.0.2")
    assert is_upgrade_supported("0.0.1", "0.1.0")
    assert not is_upgrade_supported("0.0.1", "1.0.0")
