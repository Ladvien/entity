# vLLM Configuration

The framework can start a vLLM server for you. Set `ENTITY_AUTO_INSTALL_VLLM=true` to download the package at runtime. Provide a specific model or let vLLM pick one based on GPU memory.

## Example

```python
from entity.defaults import load_defaults

resources = load_defaults()
```

The call checks for vLLM and installs it if missing. A local server is launched automatically and shut down when the process exits.

## Troubleshooting

* **No GPU detected** – vLLM falls back to CPU mode. Performance will be slow.
* **Port in use** – set `ENTITY_VLLM_PORT` to an open port.
* **Installation fails** – install vLLM manually with `pip install vllm` and rerun your script.
