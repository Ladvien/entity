# Entity Training Plugin

A fine-tuning plugin for the Entity Framework that enables training and fine-tuning of language models using GPU acceleration.

## 🎯 Purpose

This plugin extends the Entity Framework to support:
- Fine-tuning pre-trained language models
- LoRA/QLoRA efficient fine-tuning
- Multi-GPU training support
- Integration with Hugging Face models
- Custom dataset preparation pipelines

## 📋 Requirements

- Python 3.11+
- CUDA-capable GPU (RTX 3090 or better recommended)
- Entity Framework ^0.0.7
- 24GB+ GPU memory for full fine-tuning
- 8GB+ GPU memory for LoRA/QLoRA

## 🚀 Installation

### As a Submodule (Recommended)

If you're using this as part of the Entity Framework:

```bash
# From the Entity Framework root directory
git submodule update --init --recursive

# Navigate to the training plugin
cd examples/entity-training

# Install dependencies
poetry install
```

### Standalone Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/entity-training.git
cd entity-training

# Install with Poetry
poetry install

# Or with pip
pip install -e .
```

## 🏗️ Project Structure

```
entity-training/
├── plugins/          # Core plugin implementations
│   ├── __init__.py
│   ├── base_training.py      # Base classes for training plugins
│   ├── dataset_loader.py     # Dataset loading and preprocessing
│   ├── model_trainer.py      # Training loop implementation
│   └── config_parser.py      # Configuration management
├── configs/          # Example training configurations
│   ├── lora_config.yaml      # LoRA fine-tuning config
│   ├── full_config.yaml      # Full fine-tuning config
│   └── qlora_config.yaml     # QLoRA 4-bit config
├── data/            # Training data directory
│   └── sample.jsonl          # Sample training data format
├── models/          # Fine-tuned model storage
├── tests/           # Plugin tests
│   ├── test_dataset_loader.py
│   ├── test_trainer.py
│   └── test_integration.py
└── scripts/         # Utility scripts
    ├── prepare_dataset.py    # Dataset preparation
    └── evaluate_model.py     # Model evaluation
```

## 💻 Basic Usage

### 1. Prepare Your Dataset

Create a JSONL file in the `data/` directory:

```json
{"input": "What is the capital of France?", "output": "Paris"}
{"input": "Explain quantum computing", "output": "Quantum computing uses..."}
```

### 2. Configure Training

Create a configuration file in `configs/`:

```yaml
# configs/my_training.yaml
plugins:
  - name: DatasetLoaderPlugin
    config:
      dataset_path: "data/my_dataset.jsonl"
      split_ratio: 0.9

  - name: ModelTrainerPlugin
    config:
      model_name: "microsoft/phi-2"
      training_args:
        batch_size: 4
        learning_rate: 5e-5
        num_epochs: 3
        gradient_accumulation_steps: 4
```

### 3. Run Training

```python
from entity.workflow.executor import WorkflowExecutor
from plugins import DatasetLoaderPlugin, ModelTrainerPlugin

# Initialize workflow
executor = WorkflowExecutor()

# Load configuration
executor.load_config("configs/my_training.yaml")

# Run training
result = await executor.run({
    "task": "train",
    "dataset": "data/my_dataset.jsonl"
})
```

### 4. Using the Fine-tuned Model

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load your fine-tuned model
model = AutoModelForCausalLM.from_pretrained("models/my-fine-tuned-model")
tokenizer = AutoTokenizer.from_pretrained("models/my-fine-tuned-model")

# Generate text
inputs = tokenizer("Question: ", return_tensors="pt")
outputs = model.generate(**inputs)
response = tokenizer.decode(outputs[0])
```

## 🔧 Advanced Features

### LoRA Fine-tuning

For memory-efficient training:

```yaml
plugins:
  - name: LoRATrainerPlugin
    config:
      r: 16  # LoRA rank
      lora_alpha: 32
      target_modules: ["q_proj", "v_proj"]
      lora_dropout: 0.1
```

### QLoRA (4-bit Quantization)

For even more memory efficiency:

```yaml
plugins:
  - name: QLoRATrainerPlugin
    config:
      load_in_4bit: true
      bnb_4bit_compute_dtype: "float16"
      bnb_4bit_quant_type: "nf4"
```

### Multi-GPU Training

```yaml
plugins:
  - name: DistributedTrainerPlugin
    config:
      num_gpus: 2
      strategy: "ddp"  # or "fsdp" for large models
```

## ⚠️ GPU Memory Requirements

| Model Size | Full Fine-tuning | LoRA | QLoRA |
|------------|-----------------|------|-------|
| 3B params  | 24GB           | 12GB | 6GB   |
| 7B params  | 48GB           | 24GB | 12GB  |
| 13B params | 80GB           | 40GB | 20GB  |

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=plugins

# Run specific test
poetry run pytest tests/test_dataset_loader.py
```

## 📝 Supported Model Formats

- Hugging Face Transformers models
- GGUF format (through converters)
- SafeTensors format
- PyTorch checkpoints

## 🔗 Links

- [Entity Framework](https://github.com/yourusername/entity)
- [Documentation](https://entity-framework.readthedocs.io)
- [Hugging Face Models](https://huggingface.co/models)

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## ⚡ Performance Tips

1. Use mixed precision training (fp16/bf16) to reduce memory usage
2. Enable gradient checkpointing for large models
3. Use LoRA/QLoRA for parameter-efficient training
4. Adjust batch size and gradient accumulation based on GPU memory
5. Use flash attention when available

## 🐛 Troubleshooting

### CUDA Out of Memory
- Reduce batch size
- Enable gradient accumulation
- Use LoRA/QLoRA instead of full fine-tuning
- Enable gradient checkpointing

### Slow Training
- Check GPU utilization with `nvidia-smi`
- Ensure data is preprocessed and cached
- Use DataLoader with multiple workers
- Enable mixed precision training

### Import Errors
- Ensure Entity Framework is installed
- Check Python version (3.11+ required)
- Verify CUDA installation matches PyTorch version

## 📊 Monitoring

Training progress can be monitored using:
- TensorBoard: `tensorboard --logdir=./runs`
- Weights & Biases: Set `WANDB_PROJECT` in `.env`
- Built-in Entity Framework metrics
