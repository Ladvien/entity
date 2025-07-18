from entity.cli import load_plugin
from entity.core.plugins import Plugin


def test_load_plugin(tmp_path):
    plugin_file = tmp_path / "plug.py"
    plugin_file.write_text(
        "from entity.core.plugins import Plugin\n"
        "class Demo(Plugin):\n"
        "    stages = []\n"
    )
    cls = load_plugin(str(plugin_file))
    assert issubclass(cls, Plugin)
    assert cls.__name__ == "Demo"
