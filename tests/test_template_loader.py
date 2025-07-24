from entity.workflow.templates import load_template


def test_load_template(tmp_path):
    wf = load_template(
        "basic",
        think_plugin="entity.plugins.defaults.ThinkPlugin",
        output_plugin="entity.plugins.defaults.OutputPlugin",
    )
    assert wf.plugins_for("think")[0].__name__ == "ThinkPlugin"
