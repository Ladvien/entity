"""Tests for Adaptive LLM Infrastructure with GPU Acceleration Detection."""

from typing import List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from entity.infrastructure.adaptive_llm_infra import (
    AccelerationType,
    AdaptiveLLMInfrastructure,
    ModelBackend,
    ModelConfig,
    PerformanceBenchmark,
)


class TestAdaptiveLLMInfrastructure:
    """Test suite for AdaptiveLLMInfrastructure."""

    @pytest.fixture
    def infrastructure(self):
        """Create infrastructure instance for testing."""
        return AdaptiveLLMInfrastructure(
            benchmark_timeout=5.0, min_tokens_per_second=10.0
        )

    @pytest.fixture
    def sample_model_configs(self) -> List[ModelConfig]:
        """Sample model configurations for testing."""
        return [
            ModelConfig(
                backend=ModelBackend.GPT_OSS_HARMONY,
                model_name="test-mxfp4-model",
                acceleration=AccelerationType.MXFP4,
                priority=1,
            ),
            ModelConfig(
                backend=ModelBackend.TRANSFORMERS_GPTQ,
                model_name="test-gptq-model",
                acceleration=AccelerationType.CUDA,
                priority=10,
            ),
            ModelConfig(
                backend=ModelBackend.CPU_FALLBACK,
                model_name="test-cpu-model",
                acceleration=AccelerationType.CPU_ONLY,
                priority=100,
            ),
        ]

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        infra = AdaptiveLLMInfrastructure()

        assert infra.benchmark_timeout == 10.0
        assert infra.min_tokens_per_second == 20.0
        assert len(infra.model_configs) > 0
        assert infra.current_backend is None
        assert infra.active_infrastructure is None
        assert infra.acceleration_type is None

    def test_init_with_custom_models(self, sample_model_configs):
        """Test initialization with custom model configurations."""
        infra = AdaptiveLLMInfrastructure(preferred_models=sample_model_configs)

        assert infra.model_configs == sample_model_configs
        assert len(infra.model_configs) == 3

    def test_get_default_model_configs(self, infrastructure):
        """Test default model configuration generation."""
        configs = infrastructure._get_default_model_configs()

        assert len(configs) >= 4  # Should have multiple fallback options

        # Check that priorities are properly set
        priorities = [config.priority for config in configs]
        assert sorted(priorities) == priorities  # Should be sorted by priority

        # Check that required backends are present
        backends = [config.backend for config in configs]
        assert ModelBackend.GPT_OSS_HARMONY in backends
        assert ModelBackend.CPU_FALLBACK in backends

    @pytest.mark.asyncio
    async def test_detect_gpu_acceleration_mxfp4(self, infrastructure):
        """Test MXFP4 acceleration detection."""
        with patch.object(infrastructure, "_test_mxfp4_support", return_value=True):
            acceleration = await infrastructure._detect_gpu_acceleration()
            assert acceleration == AccelerationType.MXFP4

    @pytest.mark.asyncio
    async def test_detect_gpu_acceleration_cuda(self, infrastructure):
        """Test CUDA acceleration detection."""
        with (
            patch.object(infrastructure, "_test_mxfp4_support", return_value=False),
            patch.object(infrastructure, "_test_cuda_support", return_value=True),
        ):
            acceleration = await infrastructure._detect_gpu_acceleration()
            assert acceleration == AccelerationType.CUDA

    @pytest.mark.asyncio
    async def test_detect_gpu_acceleration_metal(self, infrastructure):
        """Test Metal acceleration detection on macOS."""
        with (
            patch.object(infrastructure, "_test_mxfp4_support", return_value=False),
            patch.object(infrastructure, "_test_cuda_support", return_value=False),
            patch("platform.system", return_value="Darwin"),
            patch.object(infrastructure, "_test_metal_support", return_value=True),
        ):
            acceleration = await infrastructure._detect_gpu_acceleration()
            assert acceleration == AccelerationType.METAL

    @pytest.mark.asyncio
    async def test_detect_gpu_acceleration_cpu_fallback(self, infrastructure):
        """Test fallback to CPU when no acceleration is available."""
        with (
            patch.object(infrastructure, "_test_mxfp4_support", return_value=False),
            patch.object(infrastructure, "_test_cuda_support", return_value=False),
            patch.object(infrastructure, "_test_metal_support", return_value=False),
            patch.object(infrastructure, "_test_opencl_support", return_value=False),
        ):
            acceleration = await infrastructure._detect_gpu_acceleration()
            assert acceleration == AccelerationType.CPU_ONLY

    @pytest.mark.asyncio
    async def test_mxfp4_support_detection(self, infrastructure):
        """Test MXFP4 support detection logic."""
        # Test when gpt_oss module is not available
        with patch("importlib.import_module", side_effect=ImportError):
            result = await infrastructure._test_mxfp4_support()
            assert result is False

        # Test when gpt_oss module is available but no mxfp4_acceleration
        mock_module = Mock()
        del mock_module.mxfp4_acceleration  # Remove the attribute
        with patch("importlib.import_module", return_value=mock_module):
            result = await infrastructure._test_mxfp4_support()
            assert result is False

        # Test when gpt_oss module has mxfp4_acceleration
        mock_module = Mock()
        mock_module.mxfp4_acceleration = True
        with patch("importlib.import_module", return_value=mock_module):
            result = await infrastructure._test_mxfp4_support()
            assert result is True

    @pytest.mark.asyncio
    async def test_cuda_support_detection(self, infrastructure):
        """Test CUDA support detection."""
        # Test when torch import fails
        with patch("builtins.__import__", side_effect=ImportError):
            result = await infrastructure._test_cuda_support()
            assert result is False

        # Test when torch is available and CUDA is available
        mock_torch = Mock()
        mock_torch.cuda.is_available.return_value = True
        modules = {"torch": mock_torch}
        with patch.dict("sys.modules", modules):
            result = await infrastructure._test_cuda_support()
            assert result is True

    @pytest.mark.asyncio
    async def test_metal_support_detection(self, infrastructure):
        """Test Metal support detection."""
        # Test when torch is not available
        with patch("builtins.__import__", side_effect=ImportError):
            result = await infrastructure._test_metal_support()
            assert result is False

        # Test when torch is available with MPS support
        mock_torch = Mock()
        mock_torch.backends.mps.is_available.return_value = True
        modules = {"torch": mock_torch}
        with patch.dict("sys.modules", modules):
            result = await infrastructure._test_metal_support()
            assert result is True

    def test_get_compatible_models_mxfp4(self, infrastructure, sample_model_configs):
        """Test compatible model filtering with MXFP4 acceleration."""
        infrastructure.model_configs = sample_model_configs
        infrastructure.acceleration_type = AccelerationType.MXFP4

        compatible = infrastructure._get_compatible_models()

        assert len(compatible) == 1
        assert compatible[0].acceleration == AccelerationType.MXFP4
        assert compatible[0].backend == ModelBackend.GPT_OSS_HARMONY

    def test_get_compatible_models_cuda(self, infrastructure, sample_model_configs):
        """Test compatible model filtering with CUDA acceleration."""
        infrastructure.model_configs = sample_model_configs
        infrastructure.acceleration_type = AccelerationType.CUDA

        compatible = infrastructure._get_compatible_models()

        assert len(compatible) == 2  # CUDA model + CPU fallback
        cuda_models = [m for m in compatible if m.acceleration == AccelerationType.CUDA]
        cpu_models = [
            m for m in compatible if m.acceleration == AccelerationType.CPU_ONLY
        ]
        assert len(cuda_models) == 1
        assert len(cpu_models) == 1

    def test_get_compatible_models_priority_sorting(
        self, infrastructure, sample_model_configs
    ):
        """Test that compatible models are sorted by priority."""
        infrastructure.model_configs = sample_model_configs
        infrastructure.acceleration_type = AccelerationType.CUDA

        compatible = infrastructure._get_compatible_models()

        # Check that priorities are in ascending order
        priorities = [model.priority for model in compatible]
        assert priorities == sorted(priorities)

    @pytest.mark.asyncio
    async def test_run_performance_test(self, infrastructure):
        """Test performance benchmarking of a model."""
        model_config = ModelConfig(
            backend=ModelBackend.GPT_OSS_HARMONY,
            model_name="test-model",
            acceleration=AccelerationType.MXFP4,
            priority=1,
        )

        with (
            patch.object(infrastructure, "_create_test_infrastructure") as mock_create,
            patch.object(
                infrastructure, "_test_harmony_model", return_value="Test response"
            ),
        ):
            mock_infra = Mock()
            mock_infra.shutdown = AsyncMock()
            mock_create.return_value = mock_infra

            benchmark = await infrastructure._run_performance_test(model_config)

            assert isinstance(benchmark, PerformanceBenchmark)
            assert benchmark.success is True
            assert benchmark.tokens_per_second > 0
            assert benchmark.latency_ms > 0

    @pytest.mark.asyncio
    async def test_run_performance_test_failure(self, infrastructure):
        """Test performance test handling of failures."""
        model_config = ModelConfig(
            backend=ModelBackend.GPT_OSS_HARMONY,
            model_name="test-model",
            acceleration=AccelerationType.MXFP4,
            priority=1,
        )

        with patch.object(
            infrastructure,
            "_create_test_infrastructure",
            side_effect=Exception("Test error"),
        ):
            benchmark = await infrastructure._run_performance_test(model_config)

            assert isinstance(benchmark, PerformanceBenchmark)
            assert benchmark.success is False
            assert benchmark.error_message == "Test error"
            assert benchmark.tokens_per_second == 0.0

    @pytest.mark.asyncio
    async def test_benchmark_and_select_best_model(
        self, infrastructure, sample_model_configs
    ):
        """Test model selection based on benchmarking results."""

        # Mock performance results - make middle model perform best
        def mock_performance_test(config):
            if config.backend == ModelBackend.TRANSFORMERS_GPTQ:
                return PerformanceBenchmark(
                    tokens_per_second=50.0,
                    latency_ms=100.0,
                    memory_usage_mb=1024.0,
                    success=True,
                )
            else:
                return PerformanceBenchmark(
                    tokens_per_second=5.0,  # Below threshold
                    latency_ms=200.0,
                    memory_usage_mb=1024.0,
                    success=True,
                )

        with patch.object(
            infrastructure, "_run_performance_test", side_effect=mock_performance_test
        ):
            best_model = await infrastructure._benchmark_and_select(
                sample_model_configs
            )

            assert best_model is not None
            assert best_model.backend == ModelBackend.TRANSFORMERS_GPTQ
            assert len(infrastructure.benchmark_results) > 0

    @pytest.mark.asyncio
    async def test_benchmark_and_select_fallback(
        self, infrastructure, sample_model_configs
    ):
        """Test fallback to highest priority model when none meet threshold."""

        def mock_poor_performance(config):
            return PerformanceBenchmark(
                tokens_per_second=5.0,  # Below threshold
                latency_ms=500.0,
                memory_usage_mb=1024.0,
                success=True,
            )

        with patch.object(
            infrastructure, "_run_performance_test", side_effect=mock_poor_performance
        ):
            best_model = await infrastructure._benchmark_and_select(
                sample_model_configs
            )

            assert best_model is not None
            assert best_model == sample_model_configs[0]  # Highest priority

    @pytest.mark.asyncio
    async def test_startup_success(self, infrastructure, sample_model_configs):
        """Test successful infrastructure startup."""
        infrastructure.model_configs = sample_model_configs

        with (
            patch.object(
                infrastructure,
                "_detect_gpu_acceleration",
                return_value=AccelerationType.MXFP4,
            ),
            patch.object(
                infrastructure,
                "_benchmark_and_select",
                return_value=sample_model_configs[0],
            ),
            patch.object(infrastructure, "_initialize_backend") as mock_init,
        ):
            await infrastructure.startup()

            assert infrastructure.acceleration_type == AccelerationType.MXFP4
            mock_init.assert_called_once_with(sample_model_configs[0])

    @pytest.mark.asyncio
    async def test_startup_no_compatible_models(self, infrastructure):
        """Test startup failure when no compatible models found."""
        with (
            patch.object(
                infrastructure,
                "_detect_gpu_acceleration",
                return_value=AccelerationType.MXFP4,
            ),
            patch.object(infrastructure, "_get_compatible_models", return_value=[]),
        ):
            with pytest.raises(RuntimeError, match="No compatible models found"):
                await infrastructure.startup()

    @pytest.mark.asyncio
    async def test_startup_no_suitable_backend(
        self, infrastructure, sample_model_configs
    ):
        """Test startup failure when no suitable backend found."""
        infrastructure.model_configs = sample_model_configs

        with (
            patch.object(
                infrastructure,
                "_detect_gpu_acceleration",
                return_value=AccelerationType.MXFP4,
            ),
            patch.object(infrastructure, "_benchmark_and_select", return_value=None),
        ):
            with pytest.raises(RuntimeError, match="No suitable model backend found"):
                await infrastructure.startup()

    @pytest.mark.asyncio
    async def test_shutdown(self, infrastructure):
        """Test infrastructure shutdown."""
        mock_active_infra = Mock()
        mock_active_infra.shutdown = AsyncMock()
        infrastructure.active_infrastructure = mock_active_infra

        await infrastructure.shutdown()

        mock_active_infra.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_with_active_infrastructure(self, infrastructure):
        """Test health check with active infrastructure."""
        mock_active_infra = Mock()
        mock_active_infra.health_check = AsyncMock(return_value=True)
        infrastructure.active_infrastructure = mock_active_infra

        result = await infrastructure.health_check()

        assert result is True
        mock_active_infra.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_no_active_infrastructure(self, infrastructure):
        """Test health check without active infrastructure."""
        result = await infrastructure.health_check()
        assert result is False

    def test_get_benchmark_results(self, infrastructure):
        """Test benchmark results retrieval."""
        infrastructure.benchmark_results = {
            ModelBackend.GPT_OSS_HARMONY: PerformanceBenchmark(
                tokens_per_second=100.0,
                latency_ms=50.0,
                memory_usage_mb=1024.0,
                success=True,
            )
        }

        results = infrastructure.get_benchmark_results()

        assert "gpt_oss_harmony" in results
        assert results["gpt_oss_harmony"]["tokens_per_second"] == 100.0
        assert results["gpt_oss_harmony"]["success"] is True

    def test_get_current_config(self, infrastructure):
        """Test current configuration retrieval."""
        infrastructure.current_backend = ModelBackend.GPT_OSS_HARMONY
        infrastructure.acceleration_type = AccelerationType.MXFP4
        infrastructure.benchmark_results = {}

        config = infrastructure.get_current_config()

        assert config["backend"] == "gpt_oss_harmony"
        assert config["acceleration"] == "mxfp4"
        assert "benchmark_results" in config

    @pytest.mark.asyncio
    async def test_create_test_infrastructure_harmony(self, infrastructure):
        """Test test infrastructure creation for harmony models."""
        model_config = ModelConfig(
            backend=ModelBackend.GPT_OSS_HARMONY,
            model_name="test-model",
            acceleration=AccelerationType.MXFP4,
            priority=1,
        )

        with patch(
            "entity.infrastructure.adaptive_llm_infra.HarmonyOSSInfrastructure"
        ) as mock_harmony:
            await infrastructure._create_test_infrastructure(model_config)

            mock_harmony.assert_called_once_with(
                model_name="test-model", temperature=0.7, max_tokens=100
            )

    @pytest.mark.asyncio
    async def test_harmony_model_testing(self, infrastructure):
        """Test harmony model performance testing."""
        mock_infra = Mock()
        result = await infrastructure._test_harmony_model(mock_infra, "test prompt")

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_standard_model_testing(self, infrastructure):
        """Test standard model performance testing."""
        mock_infra = Mock()
        result = await infrastructure._test_standard_model(mock_infra, "test prompt")

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_initialize_backend_harmony(self, infrastructure):
        """Test backend initialization for harmony models."""
        model_config = ModelConfig(
            backend=ModelBackend.GPT_OSS_HARMONY,
            model_name="test-model",
            acceleration=AccelerationType.MXFP4,
            priority=1,
            temperature=0.8,
            max_tokens=1000,
        )

        mock_infra = Mock()
        mock_infra.startup = AsyncMock()

        with patch(
            "entity.infrastructure.adaptive_llm_infra.HarmonyOSSInfrastructure",
            return_value=mock_infra,
        ):
            await infrastructure._initialize_backend(model_config)

            assert infrastructure.current_backend == ModelBackend.GPT_OSS_HARMONY
            assert infrastructure.active_infrastructure == mock_infra
            mock_infra.startup.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_backend_standard(self, infrastructure):
        """Test backend initialization for standard models."""
        model_config = ModelConfig(
            backend=ModelBackend.TRANSFORMERS_GPTQ,
            model_name="test-model",
            acceleration=AccelerationType.CUDA,
            priority=10,
        )

        mock_infra = Mock()
        mock_infra.startup = AsyncMock()

        with patch(
            "entity.infrastructure.adaptive_llm_infra.StandardModelInfrastructure",
            return_value=mock_infra,
        ):
            await infrastructure._initialize_backend(model_config)

            assert infrastructure.current_backend == ModelBackend.TRANSFORMERS_GPTQ
            assert infrastructure.active_infrastructure == mock_infra
            mock_infra.startup.assert_called_once()


class TestAccelerationType:
    """Test AccelerationType enum."""

    def test_acceleration_types(self):
        """Test all acceleration types are defined."""
        assert AccelerationType.MXFP4.value == "mxfp4"
        assert AccelerationType.CUDA.value == "cuda"
        assert AccelerationType.METAL.value == "metal"
        assert AccelerationType.OPENCL.value == "opencl"
        assert AccelerationType.CPU_ONLY.value == "cpu_only"


class TestModelBackend:
    """Test ModelBackend enum."""

    def test_model_backends(self):
        """Test all model backends are defined."""
        assert ModelBackend.GPT_OSS_HARMONY.value == "gpt_oss_harmony"
        assert ModelBackend.TRANSFORMERS_GPTQ.value == "transformers_gptq"
        assert ModelBackend.TRANSFORMERS_AWQ.value == "transformers_awq"
        assert ModelBackend.TRANSFORMERS_GGML.value == "transformers_ggml"
        assert ModelBackend.CPU_FALLBACK.value == "cpu_fallback"


class TestModelConfig:
    """Test ModelConfig dataclass."""

    def test_model_config_creation(self):
        """Test ModelConfig creation and defaults."""
        config = ModelConfig(
            backend=ModelBackend.GPT_OSS_HARMONY,
            model_name="test-model",
            acceleration=AccelerationType.MXFP4,
        )

        assert config.backend == ModelBackend.GPT_OSS_HARMONY
        assert config.model_name == "test-model"
        assert config.acceleration == AccelerationType.MXFP4
        assert config.quantization is None
        assert config.max_tokens == 2048
        assert config.temperature == 0.7
        assert config.priority == 100


class TestPerformanceBenchmark:
    """Test PerformanceBenchmark dataclass."""

    def test_performance_benchmark_creation(self):
        """Test PerformanceBenchmark creation."""
        benchmark = PerformanceBenchmark(
            tokens_per_second=50.0,
            latency_ms=100.0,
            memory_usage_mb=1024.0,
            success=True,
            error_message="test error",
        )

        assert benchmark.tokens_per_second == 50.0
        assert benchmark.latency_ms == 100.0
        assert benchmark.memory_usage_mb == 1024.0
        assert benchmark.success is True
        assert benchmark.error_message == "test error"

    def test_performance_benchmark_defaults(self):
        """Test PerformanceBenchmark with default values."""
        benchmark = PerformanceBenchmark(
            tokens_per_second=50.0,
            latency_ms=100.0,
            memory_usage_mb=1024.0,
            success=True,
        )

        assert benchmark.error_message is None
