from entity.workflow.templates import load_template


def test_load_template(tmp_path):
    wf = load_template(
        "basic",
        resources={},
        think_plugin="entity.plugins.defaults.ThinkPlugin",
        output_plugin="entity.plugins.defaults.OutputPlugin",
    )
    assert wf.plugins_for("think")[0].__class__.__name__ == "ThinkPlugin"
