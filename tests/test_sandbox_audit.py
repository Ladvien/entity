from plugins.contrib.infrastructure.sandbox import PluginAuditor


def test_audit_detects_invalid_resources(tmp_path):
    manifest = """
resources = ["net", "disk", "evil"]
"""
    (tmp_path / "plugin.toml").write_text(manifest)
    auditor = PluginAuditor(["net", "disk"])
    assert auditor.audit(str(tmp_path)) == ["evil"]
