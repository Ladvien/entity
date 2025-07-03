
```{include} ../../README.md
:relative-images:
:start-after: <!-- start quick_start -->
:end-before: <!-- end quick_start -->
```

## Examples

For deployment details on Amazon Web Services, see [Deployment on AWS](deploy_aws.md).
- [`vector_memory_pipeline.py`](../../examples/pipelines/vector_memory_pipeline.py)
  demonstrates using Postgres, an LLM with the Ollama provider, and simple vector memory.
- [`memory_composition_pipeline.py`](../../examples/pipelines/memory_composition_pipeline.py)
  shows how to compose the ``MemoryResource`` with SQLite, PGVector, and a local
  filesystem backend.
- [AWS deployment guide](deploy_aws.md) shows how to provision AWS resources with the Terraform Python SDK.
- **Postgres connection pooling**
  ```python
  PostgresResource(
      {
          "host": "localhost",
          "name": "dev_db",
          "username": "agent",
          "password": "",
          "pool_min_size": 1,
          "pool_max_size": 5,
      }
  )
  ```
- **Storage interface usage**
  ```python
  db = context.get_resource("database")
  await db.save_history(
      context.pipeline_id,
      context.get_conversation_history(),
  )
  ```

## Runtime Configuration Reload

Reload plugin configuration on the fly:

```bash
python -m src.cli reload-config updated.yaml
```

This feature highlights **Dynamic Configuration Updates** and keeps
long-running agents responsive.

```{toctree}
:hidden:

quick_start
config
context
plugin_guide
advanced_usage
<<<<<<< HEAD
aws_deployment
=======
deploy_aws
>>>>>>> 7966420636c5eba71f9deaf1bc4b88c234ab703d
principle_checklist
deploy_aws
apidocs/index
```

