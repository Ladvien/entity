
## Epic: Create Entity Framework Fine-Tuning Plugin

### ✅ Story 1: Set Up Git Submodule Repository [COMPLETED 2025-08-10]
**Status:** Complete - Created entity-training plugin structure in examples/entity-training

---

### Story 2: Create Base Training Plugin Classes
**Priority:** High
**Story Points:** 5
**Assignee:** Junior Developer

**Story Description:**
Create the foundational plugin classes that follow Entity Framework patterns. These will handle dataset loading, training configuration, and model management.

**Background Context:**
Entity Framework uses a 6-stage pipeline. We need to create plugins that fit into this pipeline naturally while handling the complexities of model fine-tuning. Each plugin should have a single responsibility.

**Acceptance Criteria:**
1. Create DatasetLoaderPlugin for INPUT stage
2. Create TrainingConfigPlugin for PARSE stage
3. Create base classes that other plugins can inherit from
4. All plugins follow Entity Framework patterns
5. Plugins have proper error handling
6. Each plugin has comprehensive docstrings

**Detailed Tasks:**

**Task 1: Create Base Training Plugin (2 hours)**
- Create file: plugins/base_training.py
- Import necessary Entity Framework classes:
  ```python
  from entity.plugins.base import Plugin
  from entity.workflow.executor import WorkflowExecutor
  from pydantic import BaseModel
  ```
- Create BaseTrainingPlugin class that extends Plugin
- Add common properties all training plugins need:
  - device (cuda/cpu detection)
  - output_dir (where to save models)
  - logging configuration
- Add helper method to check GPU availability
- Add helper method to format memory usage (bytes to GB)
- Add docstrings explaining the purpose and usage
- Commit with message: "Create base training plugin class"

**Task 2: Implement DatasetLoaderPlugin (3 hours)**
- Create file: plugins/dataset_loader.py
- This plugin runs in the INPUT stage
- Create ConfigModel with these fields:
  - dataset_path (string or list of strings)
  - dataset_format (choices: "alpaca", "sharegpt", "openai", "json")
  - max_samples (optional int for testing)
  - validation_split (float, default 0.1)
  - shuffle (boolean, default True)
  - seed (int for reproducibility)
- Implement _execute_impl method that:
  - Loads dataset from specified path
  - Auto-detects format if not specified
  - Validates the data structure
  - Splits into train/validation sets
  - Stores dataset info in context memory
  - Returns summary message about loaded data
- Add format detection logic:
  - Check for 'instruction'/'input'/'output' keys (Alpaca)
  - Check for 'conversations' key (ShareGPT)
  - Check for 'messages' key (OpenAI)
- Add error handling for:
  - File not found
  - Invalid JSON
  - Unsupported format
  - Empty dataset
- Write comprehensive docstrings
- Commit with message: "Implement DatasetLoaderPlugin"

**Task 3: Create TrainingConfigPlugin (3 hours)**
- Create file: plugins/training_config.py
- This plugin runs in the PARSE stage
- Create ConfigModel with training hyperparameters:
  - model_name_or_path (string)
  - training_method (choices: "full", "lora", "qlora")
  - learning_rate (float with validation)
  - batch_size (int)
  - gradient_accumulation_steps (int)
  - num_epochs (int)
  - max_steps (optional int)
  - warmup_steps (int)
  - logging_steps (int)
  - save_steps (int)
  - evaluation_steps (int)
- Add LoRA-specific configuration:
  - lora_r (int, default 16)
  - lora_alpha (int, default 32)
  - lora_dropout (float, default 0.1)
  - target_modules (list of strings)
- Add quantization configuration:
  - load_in_4bit (boolean)
  - bnb_4bit_compute_dtype (string)
  - bnb_4bit_use_double_quant (boolean)
- Implement _execute_impl method that:
  - Validates configuration based on available GPU memory
  - Calculates if model will fit in VRAM
  - Adjusts batch size if needed
  - Stores configuration in context
  - Returns configuration summary
- Add memory estimation logic:
  - Estimate model size based on parameter count
  - Account for LoRA overhead
  - Account for optimizer states
  - Warn if configuration might cause OOM
- Commit with message: "Create TrainingConfigPlugin"

**Task 4: Create Plugin Registry (2 hours)**
- Create file: plugins/__init__.py
- Import all plugin classes
- Create AVAILABLE_PLUGINS dictionary mapping names to classes
- Create a function get_plugin(name) that returns plugin class
- Create a function list_plugins() that returns available plugins
- Add documentation about each plugin's purpose
- Create plugin discovery mechanism for workflow configs
- Commit with message: "Create plugin registry"

**Task 5: Add Plugin Utilities (2 hours)**
- Create file: plugins/utils.py
- Add function to detect GPU and available memory
- Add function to convert dataset formats
- Add function to estimate training time
- Add function to calculate number of training steps
- Add logging utilities that work with Entity's logging
- Add progress bar utilities for training
- Create model size estimation functions
- Add helper for checkpoint management
- Commit with message: "Add plugin utility functions"

**Task 6: Write Plugin Tests (2 hours)**
- Create file: tests/test_plugins.py
- Write test for DatasetLoaderPlugin:
  - Test loading each supported format
  - Test format auto-detection
  - Test validation split
  - Test error handling for invalid data
- Write test for TrainingConfigPlugin:
  - Test configuration validation
  - Test memory estimation
  - Test automatic batch size adjustment
- Use pytest-asyncio for async test methods
- Mock GPU availability for CI/CD environments
- Commit with message: "Add plugin unit tests"

---

### Story 3: Implement Core Training Execution Plugin
**Priority:** High
**Story Points:** 8
**Assignee:** Junior Developer

**Story Description:**
Create the main FineTuningPlugin that executes the actual model training. This is the most complex plugin and runs in the DO stage of the Entity pipeline.

**Background Context:**
This plugin needs to handle model loading, training loop execution, checkpointing, and progress tracking while fitting within Entity Framework's patterns. It should support both full fine-tuning and LoRA/QLoRA methods.

**Acceptance Criteria:**
1. Plugin successfully loads models from HuggingFace or local paths
2. Supports full fine-tuning, LoRA, and QLoRA training methods
3. Implements proper checkpointing during training
4. Tracks and reports training metrics
5. Handles interruptions gracefully
6. Works within RTX 3090's 24GB memory constraint

**Detailed Tasks:**

**Task 1: Create FineTuningPlugin Structure (2 hours)**
- Create file: plugins/fine_tuning.py
- Import required libraries:
  - Entity Framework components
  - Transformers (AutoModelForCausalLM, AutoTokenizer, Trainer)
  - PEFT (LoraConfig, get_peft_model, TaskType)
  - Accelerate components
  - BitsAndBytes for quantization
- Create FineTuningPlugin class extending ToolPlugin
- Set supported_stages = [WorkflowExecutor.DO]
- Set dependencies = ["memory", "logging"]
- Create ConfigModel with:
  - resume_from_checkpoint (optional string)
  - output_dir (string)
  - push_to_hub (boolean)
  - hub_model_id (optional string)
  - gradient_checkpointing (boolean)
  - optim (string, default "adamw_torch")
  - max_grad_norm (float)
  - fp16 (boolean)
  - bf16 (boolean)
- Add class properties for model, tokenizer, trainer
- Commit with message: "Create FineTuningPlugin structure"

**Task 2: Implement Model Loading (3 hours)**
- Create method: _load_model_and_tokenizer()
- Get configuration from context memory (set by TrainingConfigPlugin)
- Implement logic for different training methods:
  - Full fine-tuning: Load model normally
  - LoRA: Load model then apply PEFT
  - QLoRA: Load with 4-bit quantization then apply PEFT
- For QLoRA, configure BitsAndBytesConfig:
  - load_in_4bit=True
  - bnb_4bit_compute_dtype=torch.float16
  - bnb_4bit_use_double_quant=True
  - bnb_4bit_quant_type="nf4"
- Add proper padding token handling
- Handle model loading errors:
  - Model not found
  - Insufficient memory
  - Incompatible model type
- Add logging for model size and memory usage
- Test with small model like "gpt2" first
- Commit with message: "Implement model loading logic"

**Task 3: Implement Data Preparation (3 hours)**
- Create method: _prepare_training_data()
- Get dataset from context memory (set by DatasetLoaderPlugin)
- Create tokenization function that handles different formats
- Implement smart batching to maximize GPU usage
- Add data collator for language modeling
- Handle different sequence lengths properly
- Add support for conversation templates
- Implement truncation and padding strategies
- Create validation dataset split
- Add data preprocessing progress bar
- Log dataset statistics (tokens, sequences, etc.)
- Commit with message: "Add data preparation logic"

**Task 4: Implement Training Loop (4 hours)**
- Create method: _train_model()
- Configure TrainingArguments with values from context
- Set up proper logging directory
- Implement custom callback for Entity Framework logging:
  - Create EntityLoggingCallback class
  - Override on_log method to send metrics to Entity's logging
  - Track loss, learning rate, epoch progress
- Initialize Trainer with:
  - Model and tokenizer
  - Training arguments
  - Train and eval datasets
  - Data collator
  - Callbacks
- Add checkpoint resumption logic
- Implement early stopping based on validation loss
- Add gradient accumulation for large batch sizes
- Handle CUDA out of memory errors:
  - Catch exception
  - Reduce batch size
  - Retry training
- Add training progress tracking
- Commit with message: "Implement training loop"

**Task 5: Implement Checkpointing System (3 hours)**
- Create method: _save_checkpoint()
- Save model weights periodically during training
- For LoRA/QLoRA, save only adapter weights
- Implement checkpoint naming convention:
  - checkpoint-{step} for intermediate
  - final-model for completed training
- Save training state for resumption:
  - Current step/epoch
  - Optimizer state
  - Learning rate scheduler state
  - Best validation loss
- Create method: _cleanup_checkpoints()
  - Keep only N best checkpoints
  - Delete old checkpoints to save space
- Add checkpoint validation:
  - Verify files saved correctly
  - Test loading checkpoint
- Store checkpoint info in Entity's memory
- Commit with message: "Add checkpointing system"

**Task 6: Implement Metrics and Reporting (2 hours)**
- Create method: _calculate_metrics()
- Track these metrics:
  - Training loss
  - Validation loss
  - Perplexity
  - Learning rate
  - GPU memory usage
  - Training speed (tokens/second)
- Create method: _generate_training_report()
- Format metrics into readable report
- Include training configuration summary
- Add comparison with baseline if available
- Store metrics in context memory for other plugins
- Create optional TensorBoard logging
- Add CSV export option for metrics
- Commit with message: "Add metrics tracking and reporting"

**Task 7: Implement Main Execution (3 hours)**
- Implement _execute_impl() method
- Retrieve configuration from context memory
- Load dataset from context memory
- Call model loading method
- Prepare training data
- Start training with error handling
- Save final model
- Generate and return training report
- Add comprehensive error handling:
  - GPU not available
  - Model too large for memory
  - Training divergence
  - Keyboard interruption
- Ensure cleanup on failure (free GPU memory)
- Return formatted success/failure message
- Commit with message: "Implement main execution logic"

**Task 8: Add Resource Management (2 hours)**
- Create method: _estimate_memory_usage()
- Calculate required VRAM for configuration
- Create method: _optimize_memory()
- Implement gradient checkpointing setup
- Clear cache between operations
- Add memory monitoring during training
- Create method: _cleanup_resources()
- Properly delete model and clear CUDA cache
- Add context manager for automatic cleanup
- Log memory usage at key points
- Commit with message: "Add resource management"

---

### Story 4: Create Model Export and Evaluation Plugins
**Priority:** Medium
**Story Points:** 5
**Assignee:** Junior Developer

**Story Description:**
Create plugins for evaluating the fine-tuned model and exporting it in various formats. These plugins run in the REVIEW and OUTPUT stages.

**Background Context:**
After training, users need to evaluate model quality and export it for use. The evaluation plugin checks if training was successful, while the export plugin handles different output formats.

**Acceptance Criteria:**
1. EvaluationPlugin assesses model quality
2. ModelExportPlugin exports in multiple formats
3. Plugins support both full models and LoRA adapters
4. Integration with Ollama format is supported
5. Merge functionality for LoRA adapters is available

**Detailed Tasks:**

**Task 1: Create EvaluationPlugin (3 hours)**
- Create file: plugins/evaluation.py
- This plugin runs in the REVIEW stage
- Create ConfigModel with:
  - eval_dataset_path (optional, uses validation split if not provided)
  - metrics_to_calculate (list: perplexity, bleu, rouge)
  - num_samples (int for quick evaluation)
  - generation_config (max_length, temperature, etc.)
- Implement evaluation methods:
  - _calculate_perplexity(): Lower is better
  - _generate_samples(): Create example outputs
  - _compare_with_base(): Compare to original model
- Load the trained model from checkpoint
- Run evaluation on test set
- Store evaluation results in context
- Generate evaluation report with:
  - Quantitative metrics
  - Sample generations
  - Comparison with base model
  - Training/validation loss curves
- Return "PASS" or "FAIL" based on thresholds
- Commit with message: "Create EvaluationPlugin"

**Task 2: Create ModelExportPlugin (3 hours)**
- Create file: plugins/model_export.py
- This plugin runs in the OUTPUT stage
- Create ConfigModel with:
  - export_format (choices: "huggingface", "gguf", "ollama", "safetensors")
  - merge_adapter (boolean, for LoRA models)
  - quantization_format (optional: "q4_0", "q5_1", "q8_0")
  - output_path (string)
- Implement export methods:
  - _export_huggingface(): Standard HF format
  - _export_gguf(): For llama.cpp compatibility
  - _export_ollama(): Create Modelfile
  - _merge_and_export(): Merge LoRA with base
- Handle different model architectures
- Add model card generation with:
  - Training configuration
  - Dataset information
  - Performance metrics
  - Usage instructions
- Implement size optimization options
- Add verification after export
- Commit with message: "Create ModelExportPlugin"

**Task 3: Create Ollama Integration (2 hours)**
- Create method: _create_ollama_model()
- Generate Modelfile with:
  - FROM statement pointing to base or GGUF
  - ADAPTER statement for LoRA weights
  - PARAMETER settings from training
  - TEMPLATE for chat format
  - SYSTEM prompt if specified
- Implement method to run ollama create command
- Add validation that model loads in Ollama
- Create example prompt test
- Document Ollama-specific limitations
- Add instructions for serving the model
- Commit with message: "Add Ollama integration"

**Task 4: Implement Push to Hub (2 hours)**
- Create method: _push_to_huggingface()
- Check for HuggingFace token in environment
- Create model card with:
  - Model description
  - Training details
  - Evaluation results
  - Usage examples
  - Limitations
- Upload model files
- Upload tokenizer files
- Upload training logs
- Create model repository if needed
- Handle private/public repository settings
- Add error handling for upload failures
- Commit with message: "Add HuggingFace Hub integration"

**Task 5: Create Inference Test Plugin (2 hours)**
- Create file: plugins/inference_test.py
- Quick plugin to test the model works
- Load exported model
- Run sample prompts
- Measure inference speed
- Check output quality
- Compare memory usage with base model
- Generate simple benchmark report
- This helps verify the export worked correctly
- Commit with message: "Create inference test plugin"

---

### Story 5: Create Example Configurations and Scripts
**Priority:** Medium
**Story Points:** 3
**Assignee:** Junior Developer

**Story Description:**
Create example configurations and helper scripts that demonstrate how to use the fine-tuning plugins effectively.

**Background Context:**
Users need clear examples showing different training scenarios. We should provide configurations for common use cases and scripts that make the plugins easy to use.

**Acceptance Criteria:**
1. At least 3 example configurations for different scenarios
2. Main training script that uses Entity Framework
3. Sample dataset included
4. Utility scripts for common tasks
5. Everything is well documented

**Detailed Tasks:**

**Task 1: Create Example Configurations (2 hours)**
- Create configs/qlora_training.yaml:
  - Uses QLoRA for memory efficiency
  - Suitable for RTX 3090
  - Conservative batch size
  - Example for 7B parameter model
- Create configs/full_training.yaml:
  - Full fine-tuning configuration
  - For smaller models (< 3B parameters)
  - Higher batch size
- Create configs/continued_training.yaml:
  - Resume from checkpoint example
  - Shows incremental training
- Each config should have:
  - Clear comments explaining choices
  - Memory requirement estimates
  - Expected training time
  - Resource specifications
- Commit with message: "Add example configurations"

**Task 2: Create Main Training Script (3 hours)**
- Create train.py in root directory
- Import Entity Framework components
- Add command-line argument parsing:
  - --config: Path to configuration file
  - --dataset: Path to dataset
  - --model: Model name or path
  - --output: Output directory
  - --resume: Resume from checkpoint
- Load Entity Framework resources
- Create agent with specified configuration
- Add interactive mode vs batch mode
- Implement progress display
- Add error handling and recovery
- Include cleanup on exit
- Add docstring with usage examples
- Commit with message: "Create main training script"

**Task 3: Create Sample Dataset (1 hour)**
- Create data/sample.jsonl with 100 examples
- Use a simple format (Alpaca style)
- Include diverse examples:
  - Question answering
  - Instruction following
  - Creative writing
  - Code generation
- Make sure examples are high quality
- Add data/prepare_dataset.py script:
  - Converts other formats to expected format
  - Validates data structure
  - Splits into train/validation
  - Calculates dataset statistics
- Document the expected format clearly
- Commit with message: "Add sample dataset"

**Task 4: Create Utility Scripts (2 hours)**
- Create scripts/estimate_memory.py:
  - Takes model name and training config
  - Estimates VRAM requirements
  - Suggests optimal settings
- Create scripts/merge_adapter.py:
  - Merges LoRA weights with base model
  - Handles different formats
  - Validates merged model
- Create scripts/convert_to_gguf.py:
  - Converts HF model to GGUF
  - Applies quantization
  - Prepares for llama.cpp
- Create scripts/benchmark.py:
  - Tests inference speed
  - Measures memory usage
  - Compares with base model
- Each script should have help text and examples
- Commit with message: "Add utility scripts"

**Task 5: Create Docker Setup (2 hours)**
- Create Dockerfile with:
  - CUDA base image
  - Python 3.11
  - All dependencies
  - Entity Framework
  - Plugin code
- Create docker-compose.yml with:
  - GPU resource allocation
  - Volume mounts for data and models
  - Environment variables
  - Network configuration
- Add .dockerignore file
- Create scripts/run_docker.sh for easy launching
- Document Docker usage in README
- Note GPU passthrough requirements
- Commit with message: "Add Docker configuration"

**Task 6: Update Documentation (2 hours)**
- Update main README with:
  - Quick start guide
  - Installation instructions
  - Basic usage example
  - Link to detailed documentation
- Create docs/TRAINING_GUIDE.md with:
  - Detailed parameter explanations
  - Memory optimization tips
  - Troubleshooting common issues
  - Performance tuning guide
- Create docs/API.md with:
  - Plugin API reference
  - Configuration schema
  - Custom plugin creation guide
- Add examples for each use case
- Include expected outputs
- Add FAQ section
- Commit with message: "Complete documentation"

---

### Story 6: Add Testing and Validation
**Priority:** Medium
**Story Points:** 3
**Assignee:** Junior Developer

**Story Description:**
Create comprehensive tests for all plugins and add validation to ensure the training pipeline works correctly.

**Background Context:**
Tests are crucial for maintaining code quality and catching issues early. We need both unit tests for individual plugins and integration tests for the full pipeline.

**Acceptance Criteria:**
1. Unit tests for each plugin with >80% coverage
2. Integration test for complete training pipeline
3. Tests can run without GPU (using mocks)
4. CI/CD configuration is provided
5. Test data and fixtures are included

**Detailed Tasks:**

**Task 1: Create Test Fixtures (2 hours)**
- Create tests/fixtures/ directory
- Add sample configuration files
- Create mock dataset (small)
- Add expected output examples
- Create mock model weights (tiny model)
- Set up pytest fixtures in conftest.py:
  - Mock Entity context
  - Mock memory resource
  - Mock logging resource
  - Sample configurations
  - Test datasets
- Document how to use fixtures
- Commit with message: "Add test fixtures"

**Task 2: Write Plugin Unit Tests (3 hours)**
- Create tests/test_dataset_loader.py:
  - Test each supported format
  - Test format detection
  - Test validation split
  - Test error cases
  - Mock file system operations
- Create tests/test_training_config.py:
  - Test configuration validation
  - Test memory estimation
  - Test auto-adjustment logic
  - Test invalid configurations
- Create tests/test_fine_tuning.py:
  - Mock model loading
  - Mock training loop
  - Test checkpoint saving
  - Test error handling
  - Use small test model
- Ensure tests work without GPU
- Aim for >80% code coverage
- Commit with message: "Add plugin unit tests"

**Task 3: Create Integration Tests (2 hours)**
- Create tests/test_integration.py
- Test full pipeline with tiny model:
  - Load dataset
  - Configure training
  - Run 1 epoch training
  - Evaluate model
  - Export model
- Use CPU-only mode for CI
- Add timeout to prevent hanging
- Test checkpoint resumption
- Test early stopping
- Verify outputs are created
- Clean up after tests
- Commit with message: "Add integration tests"

**Task 4: Set Up GitHub Actions (2 hours)**
- Create .github/workflows/test.yml
- Configure Python 3.11 environment
- Install Poetry and dependencies
- Run linting (ruff)
- Run formatting check (black)
- Run unit tests
- Run integration tests
- Generate coverage report
- Upload coverage to service (optional)
- Cache dependencies for speed
- Run on push and pull requests
- Commit with message: "Add CI/CD workflow"

**Task 5: Add Validation and Monitoring (1 hour)**
- Create plugins/validators.py
- Add dataset validation functions
- Add model output validation
- Add checkpoint integrity checks
- Create monitoring utilities:
  - Memory usage tracker
  - Training progress logger
  - Loss curve plotter
- Add smoke test script
- Document validation steps
- Commit with message: "Add validation utilities"
