import json
from pathlib import Path

import yaml

from pipeline.config import ConfigLoader
from pipeline.workflow import Workflow


def test_workflow_roundtrip(tmp_path: Path) -> None:
    wf_data = {"parse": ["a"], "think": ["b"], "deliver": ["c"]}
    wf_yaml = tmp_path / "wf.yaml"
    wf_json = tmp_path / "wf.json"
    wf_yaml.write_text(yaml.dump(wf_data, sort_keys=False))
    wf_json.write_text(json.dumps(wf_data))

    wf_from_yaml = Workflow.from_dict(yaml.safe_load(wf_yaml.read_text()))
    wf_from_json = Workflow.from_dict(json.loads(wf_json.read_text()))
    assert wf_from_yaml.to_dict() == wf_data
    assert wf_from_json.to_dict() == wf_data

    cfg_yaml = tmp_path / "cfg.yml"
    cfg_yaml.write_text(yaml.dump({"workflow": str(wf_yaml)}, sort_keys=False))
    cfg_json = tmp_path / "cfg.json"
    cfg_json.write_text(json.dumps({"workflow": str(wf_json)}))

    loaded_yaml = ConfigLoader.from_yaml(cfg_yaml)
    loaded_json = ConfigLoader.from_json(cfg_json)
    loaded_dict = ConfigLoader.from_dict({"workflow": wf_data})

    assert loaded_yaml["workflow"].to_dict() == wf_data
    assert loaded_json["workflow"].to_dict() == wf_data
    assert loaded_dict["workflow"].to_dict() == wf_data
