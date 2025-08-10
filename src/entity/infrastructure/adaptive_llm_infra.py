"""Adaptive LLM Infrastructure with GPU Acceleration Detection and Fallback.

This module provides automatic fallback between gpt-oss MXFP4 models and
standard transformers models based on GPU acceleration availability and performance.
"""

from __future__ import annotations

import asyncio
import logging
import platform
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .base import BaseInfrastructure
from .harmony_oss_infra import HarmonyOSSInfrastructure


class AccelerationType(Enum):
    """Types of GPU acceleration supported."""

    MXFP4 = "mxfp4"
    CUDA = "cuda"
    METAL = "metal"  # Apple Silicon
    OPENCL = "opencl"
    CPU_ONLY = "cpu_only"


class ModelBackend(Enum):
    """Supported model backends."""

    GPT_OSS_HARMONY = "gpt_oss_harmony"
    TRANSFORMERS_GPTQ = "transformers_gptq"
    TRANSFORMERS_AWQ = "transformers_awq"
    TRANSFORMERS_GGML = "transformers_ggml"
    CPU_FALLBACK = "cpu_fallback"


@dataclass
class PerformanceBenchmark:
    """Results from model performance testing."""

    tokens_per_second: float
    latency_ms: float
    memory_usage_mb: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class ModelConfig:
    """Configuration for a specific model backend."""

    backend: ModelBackend
    model_name: str
    acceleration: AccelerationType
    quantization: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    priority: int = 100  # Lower = higher priority


class AdaptiveLLMInfrastructure(BaseInfrastructure):
    """Adaptive LLM infrastructure with automatic backend selection.

    This infrastructure automatically detects GPU acceleration capabilities
    and selects the best available model backend for optimal performance.
    """

    def __init__(
        self,
        preferred_models: Optional[List[ModelConfig]] = None,
        benchmark_timeout: float = 10.0,
        min_tokens_per_second: float = 20.0,
        **kwargs,
    ):
        """Initialize adaptive LLM infrastructure.

        Args:
            preferred_models: List of model configurations in order of preference
            benchmark_timeout: Timeout for performance benchmarking in seconds
            min_tokens_per_second: Minimum acceptable tokens/second performance
            **kwargs: Additional arguments passed to BaseInfrastructure
        """
        super().__init__(**kwargs)

        self.benchmark_timeout = benchmark_timeout
        self.min_tokens_per_second = min_tokens_per_second

        # Default model configurations if none provided
        self.model_configs = preferred_models or self._get_default_model_configs()

        # Runtime state
        self.current_backend: Optional[ModelBackend] = None
        self.active_infrastructure: Optional[BaseInfrastructure] = None
        self.acceleration_type: Optional[AccelerationType] = None
        self.benchmark_results: Dict[ModelBackend, PerformanceBenchmark] = {}

        self.logger = logging.getLogger(__name__)

    def _get_default_model_configs(self) -> List[ModelConfig]:
        """Get default model configurations for different scenarios."""
        configs = [
            # Primary: GPT-OSS with MXFP4 (highest priority if available)
            ModelConfig(
                backend=ModelBackend.GPT_OSS_HARMONY,
                model_name="gpt-oss-20b-mxfp4",
                acceleration=AccelerationType.MXFP4,
                priority=1,
            ),
            # Fallback 1: GPTQ quantized models
            ModelConfig(
                backend=ModelBackend.TRANSFORMERS_GPTQ,
                model_name="TheBloke/gpt-oss-20b-GPTQ",
                acceleration=AccelerationType.CUDA,
                quantization="gptq",
                priority=10,
            ),
            # Fallback 2: AWQ quantized models
            ModelConfig(
                backend=ModelBackend.TRANSFORMERS_AWQ,
                model_name="casperhansen/gpt-oss-20b-awq",
                acceleration=AccelerationType.CUDA,
                quantization="awq",
                priority=20,
            ),
            # Fallback 3: GGML for Apple Silicon
            ModelConfig(
                backend=ModelBackend.TRANSFORMERS_GGML,
                model_name="TheBloke/gpt-oss-20b-GGML",
                acceleration=AccelerationType.METAL,
                quantization="q4_0",
                priority=30,
            ),
            # Last resort: CPU-only
            ModelConfig(
                backend=ModelBackend.CPU_FALLBACK,
                model_name="microsoft/DialoGPT-medium",  # Smaller model for CPU
                acceleration=AccelerationType.CPU_ONLY,
                priority=100,
            ),
        ]

        return configs

    async def startup(self) -> None:
        """Initialize the adaptive infrastructure by detecting optimal backend."""
        await super().startup()

        self.logger.info("Starting adaptive LLM infrastructure detection...")

        # Detect available acceleration
        self.acceleration_type = await self._detect_gpu_acceleration()
        self.logger.info(f"Detected acceleration: {self.acceleration_type}")

        # Find compatible models
        compatible_models = self._get_compatible_models()
        if not compatible_models:
            raise RuntimeError("No compatible models found for current hardware")

        # Benchmark and select best model
        best_model = await self._benchmark_and_select(compatible_models)
        if not best_model:
            raise RuntimeError("No suitable model backend found")

        # Initialize selected backend
        await self._initialize_backend(best_model)

        self.logger.info(
            f"Adaptive LLM infrastructure ready with {self.current_backend}"
        )

    async def shutdown(self) -> None:
        """Shutdown the active infrastructure."""
        if self.active_infrastructure:
            await self.active_infrastructure.shutdown()
        await super().shutdown()

    async def health_check(self) -> bool:
        """Check if the active infrastructure is healthy."""
        if not self.active_infrastructure:
            return False
        return await self.active_infrastructure.health_check()

    async def _detect_gpu_acceleration(self) -> AccelerationType:
        """Detect available GPU acceleration type."""
        try:
            # Check for MXFP4 support (placeholder - would need actual detection)
            if await self._test_mxfp4_support():
                return AccelerationType.MXFP4

            # Check for CUDA
            if await self._test_cuda_support():
                return AccelerationType.CUDA

            # Check for Apple Metal (macOS)
            if platform.system() == "Darwin" and await self._test_metal_support():
                return AccelerationType.METAL

            # Check for OpenCL
            if await self._test_opencl_support():
                return AccelerationType.OPENCL

        except Exception as e:
            self.logger.warning(f"GPU detection failed: {e}")

        # Fallback to CPU
        return AccelerationType.CPU_ONLY

    async def _test_mxfp4_support(self) -> bool:
        """Test MXFP4 acceleration support (placeholder implementation)."""
        try:
            # This would be replaced with actual MXFP4 detection
            # For now, we'll simulate by checking for specific libraries
            import importlib

            # Check if gpt-oss library with MXFP4 support is available
            try:
                gpt_oss = importlib.import_module("gpt_oss")
                return hasattr(gpt_oss, "mxfp4_acceleration")
            except ImportError:
                return False

        except Exception:
            return False

    async def _test_cuda_support(self) -> bool:
        """Test CUDA acceleration support."""
        try:
            import torch

            return torch.cuda.is_available()
        except (ImportError, AttributeError):
            return False

    async def _test_metal_support(self) -> bool:
        """Test Metal acceleration support (Apple Silicon)."""
        try:
            import torch

            return hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        except (ImportError, AttributeError):
            return False

    async def _test_opencl_support(self) -> bool:
        """Test OpenCL acceleration support."""
        try:
            import pyopencl as cl

            platforms = cl.get_platforms()
            return len(platforms) > 0
        except ImportError:
            return False

    def _get_compatible_models(self) -> List[ModelConfig]:
        """Get models compatible with detected acceleration."""
        compatible = []

        for config in self.model_configs:
            if config.acceleration == self.acceleration_type:
                compatible.append(config)
            elif (
                config.acceleration == AccelerationType.CPU_ONLY
                and self.acceleration_type != AccelerationType.MXFP4
            ):
                # CPU fallback is always compatible (except when MXFP4 is available)
                compatible.append(config)

        # Sort by priority (lower number = higher priority)
        return sorted(compatible, key=lambda x: x.priority)

    async def _benchmark_and_select(
        self, models: List[ModelConfig]
    ) -> Optional[ModelConfig]:
        """Benchmark compatible models and select the best one."""
        best_model = None
        best_performance = 0.0

        for model_config in models[:3]:  # Test top 3 candidates
            try:
                self.logger.info(f"Benchmarking {model_config.backend}...")

                # Run performance test
                benchmark = await self._run_performance_test(model_config)
                self.benchmark_results[model_config.backend] = benchmark

                if (
                    benchmark.success
                    and benchmark.tokens_per_second >= self.min_tokens_per_second
                ):
                    if benchmark.tokens_per_second > best_performance:
                        best_performance = benchmark.tokens_per_second
                        best_model = model_config

                self.logger.info(
                    f"Benchmark result for {model_config.backend}: "
                    f"{benchmark.tokens_per_second:.1f} tokens/sec"
                )

            except Exception as e:
                self.logger.warning(f"Benchmark failed for {model_config.backend}: {e}")
                self.benchmark_results[model_config.backend] = PerformanceBenchmark(
                    tokens_per_second=0.0,
                    latency_ms=0.0,
                    memory_usage_mb=0.0,
                    success=False,
                    error_message=str(e),
                )

        # If no model meets performance threshold, use highest priority compatible model
        if not best_model and models:
            best_model = models[0]
            self.logger.warning(
                f"No model met performance threshold, using fallback: {best_model.backend}"
            )

        return best_model

    async def _run_performance_test(
        self, model_config: ModelConfig
    ) -> PerformanceBenchmark:
        """Run performance test on a model configuration."""
        start_time = time.time()

        try:
            # Create temporary infrastructure for testing
            test_infra = await self._create_test_infrastructure(model_config)

            # Test prompt
            test_prompt = (
                "What is the capital of France? Please provide a brief explanation."
            )

            # Measure performance
            generation_start = time.time()

            # Simulate model generation (would be actual model call)
            if model_config.backend == ModelBackend.GPT_OSS_HARMONY:
                result = await self._test_harmony_model(test_infra, test_prompt)
            else:
                result = await self._test_standard_model(test_infra, test_prompt)

            generation_time = time.time() - generation_start

            # Calculate metrics
            token_count = len(result.split()) if result else 0  # Rough token estimate
            tokens_per_second = (
                token_count / generation_time if generation_time > 0 else 0
            )
            latency_ms = generation_time * 1000

            # Memory usage (simplified)
            memory_usage_mb = 1024  # Placeholder

            # Cleanup test infrastructure
            if hasattr(test_infra, "shutdown"):
                await test_infra.shutdown()

            return PerformanceBenchmark(
                tokens_per_second=tokens_per_second,
                latency_ms=latency_ms,
                memory_usage_mb=memory_usage_mb,
                success=True,
            )

        except Exception as e:
            elapsed_time = time.time() - start_time
            return PerformanceBenchmark(
                tokens_per_second=0.0,
                latency_ms=elapsed_time * 1000,
                memory_usage_mb=0.0,
                success=False,
                error_message=str(e),
            )

    async def _create_test_infrastructure(self, model_config: ModelConfig) -> Any:
        """Create a test infrastructure instance for benchmarking."""
        if model_config.backend == ModelBackend.GPT_OSS_HARMONY:
            # Create harmony infrastructure instance
            return HarmonyOSSInfrastructure(
                model_name=model_config.model_name,
                temperature=model_config.temperature,
                max_tokens=min(100, model_config.max_tokens),  # Small for testing
            )
        else:
            # For other backends, create mock infrastructure
            return MockInfrastructure(model_config)

    async def _test_harmony_model(self, infrastructure: Any, prompt: str) -> str:
        """Test harmony model performance."""
        # This would be actual harmony model testing
        await asyncio.sleep(0.1)  # Simulate processing time
        return (
            "Paris is the capital of France. It is known for its culture and history."
        )

    async def _test_standard_model(self, infrastructure: Any, prompt: str) -> str:
        """Test standard transformers model performance."""
        # This would be actual transformers model testing
        await asyncio.sleep(0.2)  # Simulate processing time
        return "The capital of France is Paris."

    async def _initialize_backend(self, model_config: ModelConfig) -> None:
        """Initialize the selected backend infrastructure."""
        self.current_backend = model_config.backend

        if model_config.backend == ModelBackend.GPT_OSS_HARMONY:
            self.active_infrastructure = HarmonyOSSInfrastructure(
                model_name=model_config.model_name,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
            )
        else:
            # For other backends, create appropriate infrastructure
            self.active_infrastructure = StandardModelInfrastructure(model_config)

        # Initialize the active infrastructure
        await self.active_infrastructure.startup()

    def get_benchmark_results(self) -> Dict[str, Dict[str, Any]]:
        """Get benchmark results for all tested models."""
        results = {}
        for backend, benchmark in self.benchmark_results.items():
            results[backend.value] = {
                "tokens_per_second": benchmark.tokens_per_second,
                "latency_ms": benchmark.latency_ms,
                "memory_usage_mb": benchmark.memory_usage_mb,
                "success": benchmark.success,
                "error_message": benchmark.error_message,
            }
        return results

    def get_current_config(self) -> Dict[str, Any]:
        """Get current active configuration."""
        return {
            "backend": self.current_backend.value if self.current_backend else None,
            "acceleration": (
                self.acceleration_type.value if self.acceleration_type else None
            ),
            "benchmark_results": self.get_benchmark_results(),
        }


class MockInfrastructure(BaseInfrastructure):
    """Mock infrastructure for testing fallback models."""

    def __init__(self, model_config: ModelConfig):
        super().__init__()
        self.model_config = model_config

    async def health_check(self) -> bool:
        return True


class StandardModelInfrastructure(BaseInfrastructure):
    """Standard transformers model infrastructure."""

    def __init__(self, model_config: ModelConfig):
        super().__init__()
        self.model_config = model_config

    async def health_check(self) -> bool:
        return True
