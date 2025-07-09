# Migrating from Experimental Features

Early versions of this project exposed several modules under the `experiments`
package. Those modules are no longer maintained and have been replaced by stable
APIs in `src/plugins` and `src/pipeline`. Follow these steps to upgrade your
project.

## 1. Update Imports

Remove any imports that reference `experiments.*` modules. Stable equivalents
exist in the `plugins.builtin` package. For example:

```python
# Old
from experiments.storage.resource import StorageResource

# New
from plugins.builtin.resources.storage import StorageResource
```

## 2. Check Configuration Files

Experimental plugins used different keys and stage names. Use the sample
`config/prod.yaml` file as a reference and adjust your own YAML accordingly.
Run the config validator to confirm:

```bash
poetry run entity-cli --config your.yaml
```

## 3. Validate Plugins

If you wrote custom plugins during the experimental phase, make sure they inherit
from the current base classes in `pipeline.base_plugins`. Then update the
`stages` list to use values from `pipeline.stages.PipelineStage`.

## 4. Verify Stored Data

Schema or format changes might have occurred. Back up your existing database or
vector store before running the new version of the agent. Then migrate your data
as needed.

By following these steps you can remove all deprecated experimental features and
rely on the stable interfaces going forward.

