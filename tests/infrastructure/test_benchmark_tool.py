"""Tests for LLM Infrastructure Benchmark Tool."""

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, Mock, patch

import pytest

from entity.infrastructure.adaptive_llm_infra import (
    AdaptiveLLMInfrastructure,
    PerformanceBenchmark,
)
from entity.infrastructure.benchmark_tool import (
    BenchmarkResult,
    BenchmarkSuite,
    LLMBenchmarkTool,
    run_benchmark_cli,
)


class TestBenchmarkSuite:
    """Test BenchmarkSuite dataclass."""

    def test_benchmark_suite_creation(self):
        """Test BenchmarkSuite creation with custom values."""
        suite = BenchmarkSuite(
            name="test_suite",
            prompts=["prompt1", "prompt2"],
            expected_min_tokens=50,
            timeout_seconds=60.0,
            repetitions=2,
        )

        assert suite.name == "test_suite"
        assert suite.prompts == ["prompt1", "prompt2"]
        assert suite.expected_min_tokens == 50
        assert suite.timeout_seconds == 60.0
        assert suite.repetitions == 2

    def test_benchmark_suite_defaults(self):
        """Test BenchmarkSuite with default values."""
        suite = BenchmarkSuite(name="test_suite", prompts=["prompt1"])

        assert suite.expected_min_tokens == 10
        assert suite.timeout_seconds == 30.0
        assert suite.repetitions == 3


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""

    def test_benchmark_result_creation(self):
        """Test BenchmarkResult creation."""
        individual_results = [
            PerformanceBenchmark(
                tokens_per_second=50.0,
                latency_ms=100.0,
                memory_usage_mb=1024.0,
                success=True,
            )
        ]

        result = BenchmarkResult(
            suite_name="test_suite",
            model_backend="gpt_oss_harmony",
            avg_tokens_per_second=50.0,
            avg_latency_ms=100.0,
            success_rate=1.0,
            memory_usage_mb=1024.0,
            total_time_seconds=0.1,
            individual_results=individual_results,
        )

        assert result.suite_name == "test_suite"
        assert result.model_backend == "gpt_oss_harmony"
        assert result.avg_tokens_per_second == 50.0
        assert result.avg_latency_ms == 100.0
        assert result.success_rate == 1.0
        assert result.memory_usage_mb == 1024.0
        assert result.total_time_seconds == 0.1
        assert len(result.individual_results) == 1


class TestLLMBenchmarkTool:
    """Test LLMBenchmarkTool class."""

    def test_init_with_default_output_dir(self):
        """Test initialization with default output directory."""
        with TemporaryDirectory():
            tool = LLMBenchmarkTool()

            # Check that default directory is created
            assert tool.output_dir == Path("./benchmark_results")
            assert len(tool.benchmark_suites) > 0

    def test_init_with_custom_output_dir(self):
        """Test initialization with custom output directory."""
        with TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "custom_results"
            tool = LLMBenchmarkTool(output_dir=custom_path)

            assert tool.output_dir == custom_path
            assert custom_path.exists()

    def test_create_default_suites(self):
        """Test default benchmark suite creation."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))
            suites = tool._create_default_suites()

            assert len(suites) == 4

            # Check suite names
            suite_names = [suite.name for suite in suites]
            assert "quick_qa" in suite_names
            assert "reasoning_tasks" in suite_names
            assert "code_generation" in suite_names
            assert "creative_writing" in suite_names

            # Check that suites have different configurations
            quick_qa = next(s for s in suites if s.name == "quick_qa")
            assert len(quick_qa.prompts) == 3
            assert quick_qa.expected_min_tokens == 20
            assert quick_qa.repetitions == 3

            reasoning = next(s for s in suites if s.name == "reasoning_tasks")
            assert len(reasoning.prompts) == 3
            assert reasoning.expected_min_tokens == 50
            assert reasoning.timeout_seconds == 45.0
            assert reasoning.repetitions == 2

    @pytest.mark.asyncio
    async def test_run_comprehensive_benchmark(self):
        """Test running comprehensive benchmark."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            # Create minimal suite for testing
            test_suite = BenchmarkSuite(
                name="test_suite", prompts=["test prompt"], repetitions=1
            )
            tool.benchmark_suites = [test_suite]

            # Mock infrastructure
            mock_infra = Mock(spec=AdaptiveLLMInfrastructure)
            mock_infra.get_current_config.return_value = {"backend": "test_backend"}

            # Mock the suite benchmark method
            mock_result = BenchmarkResult(
                suite_name="test_suite",
                model_backend="test_backend",
                avg_tokens_per_second=50.0,
                avg_latency_ms=100.0,
                success_rate=1.0,
                memory_usage_mb=1024.0,
                total_time_seconds=0.1,
                individual_results=[],
            )

            with (
                patch.object(tool, "_run_suite_benchmark", return_value=[mock_result]),
                patch.object(tool, "_save_results") as mock_save,
            ):
                results = await tool.run_comprehensive_benchmark(mock_infra)

                assert "test_suite" in results
                assert len(results["test_suite"]) == 1
                assert results["test_suite"][0] == mock_result
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_suite_benchmark(self):
        """Test running benchmark for a specific suite."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            suite = BenchmarkSuite(
                name="test_suite", prompts=["prompt1", "prompt2"], repetitions=1
            )

            mock_infra = Mock(spec=AdaptiveLLMInfrastructure)
            mock_infra.get_current_config.return_value = {"backend": "test_backend"}

            mock_benchmark = PerformanceBenchmark(
                tokens_per_second=50.0,
                latency_ms=100.0,
                memory_usage_mb=1024.0,
                success=True,
            )

            with patch.object(
                tool, "_run_single_benchmark", return_value=mock_benchmark
            ):
                results = await tool._run_suite_benchmark(mock_infra, suite)

                assert len(results) == 2  # Two prompts
                for result in results:
                    assert isinstance(result, BenchmarkResult)
                    assert result.suite_name == "test_suite"
                    assert result.model_backend == "test_backend"
                    assert result.avg_tokens_per_second == 50.0
                    assert result.success_rate == 1.0

    @pytest.mark.asyncio
    async def test_run_suite_benchmark_with_failures(self):
        """Test suite benchmark handling of failures."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            suite = BenchmarkSuite(
                name="test_suite", prompts=["prompt1"], repetitions=2
            )

            mock_infra = Mock(spec=AdaptiveLLMInfrastructure)
            mock_infra.get_current_config.return_value = {"backend": "test_backend"}

            # First call succeeds, second fails
            successful_benchmark = PerformanceBenchmark(
                tokens_per_second=50.0,
                latency_ms=100.0,
                memory_usage_mb=1024.0,
                success=True,
            )

            def side_effect(*args, **kwargs):
                if not hasattr(side_effect, "call_count"):
                    side_effect.call_count = 0
                side_effect.call_count += 1

                if side_effect.call_count == 1:
                    return successful_benchmark
                else:
                    raise Exception("Test failure")

            with patch.object(tool, "_run_single_benchmark", side_effect=side_effect):
                results = await tool._run_suite_benchmark(mock_infra, suite)

                assert len(results) == 1
                result = results[0]
                assert result.success_rate == 0.5  # 1 success out of 2 repetitions

    @pytest.mark.asyncio
    async def test_run_single_benchmark(self):
        """Test running a single benchmark test."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            mock_infra = Mock(spec=AdaptiveLLMInfrastructure)

            benchmark = await tool._run_single_benchmark(mock_infra, "test prompt", 5.0)

            assert isinstance(benchmark, PerformanceBenchmark)
            assert benchmark.success is True
            assert benchmark.tokens_per_second > 0
            assert benchmark.latency_ms > 0
            assert benchmark.memory_usage_mb == 512  # Simulated value

    @pytest.mark.asyncio
    async def test_run_single_benchmark_timeout(self):
        """Test single benchmark with timeout."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            mock_infra = Mock(spec=AdaptiveLLMInfrastructure)

            # Use very short timeout and long processing time to trigger timeout
            with patch("asyncio.sleep", side_effect=asyncio.TimeoutError):
                benchmark = await tool._run_single_benchmark(
                    mock_infra,
                    "test prompt",
                    0.001,  # Very short timeout
                )

                assert isinstance(benchmark, PerformanceBenchmark)
                assert benchmark.success is False
                assert benchmark.error_message == "Timeout exceeded"
                assert benchmark.tokens_per_second == 0.0

    @pytest.mark.asyncio
    async def test_save_results(self):
        """Test saving benchmark results to JSON file."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            individual_result = PerformanceBenchmark(
                tokens_per_second=50.0,
                latency_ms=100.0,
                memory_usage_mb=1024.0,
                success=True,
            )

            benchmark_result = BenchmarkResult(
                suite_name="test_suite",
                model_backend="test_backend",
                avg_tokens_per_second=50.0,
                avg_latency_ms=100.0,
                success_rate=1.0,
                memory_usage_mb=1024.0,
                total_time_seconds=0.1,
                individual_results=[individual_result],
            )

            results = {"test_suite": [benchmark_result]}

            await tool._save_results(results)

            # Check that file was created
            json_files = list(Path(temp_dir).glob("benchmark_results_*.json"))
            assert len(json_files) == 1

            # Check file contents
            with open(json_files[0], "r") as f:
                saved_data = json.load(f)

            assert "test_suite" in saved_data
            assert len(saved_data["test_suite"]) == 1
            assert saved_data["test_suite"][0]["suite_name"] == "test_suite"
            assert saved_data["test_suite"][0]["avg_tokens_per_second"] == 50.0

    def test_generate_report(self):
        """Test generating human-readable benchmark report."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            individual_result = PerformanceBenchmark(
                tokens_per_second=50.0,
                latency_ms=100.0,
                memory_usage_mb=1024.0,
                success=True,
            )

            benchmark_result = BenchmarkResult(
                suite_name="test_suite",
                model_backend="test_backend",
                avg_tokens_per_second=50.0,
                avg_latency_ms=100.0,
                success_rate=1.0,
                memory_usage_mb=1024.0,
                total_time_seconds=0.1,
                individual_results=[individual_result],
            )

            results = {"test_suite": [benchmark_result]}

            report = tool.generate_report(results)

            assert "LLM INFRASTRUCTURE BENCHMARK REPORT" in report
            assert "OVERALL SUMMARY" in report
            assert "Average Tokens/Second: 50.00" in report
            assert "Average Latency: 100.0ms" in report
            assert "Overall Success Rate: 100.0%" in report
            assert "SUITE: TEST_SUITE" in report
            assert "Test 1:" in report

    def test_generate_report_empty_results(self):
        """Test report generation with empty results."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            results = {}
            report = tool.generate_report(results)

            assert "LLM INFRASTRUCTURE BENCHMARK REPORT" in report
            assert "OVERALL SUMMARY" not in report  # No summary for empty results

    def test_generate_report_multiple_suites(self):
        """Test report generation with multiple test suites."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            # Create results for multiple suites
            result1 = BenchmarkResult(
                suite_name="suite1",
                model_backend="backend1",
                avg_tokens_per_second=30.0,
                avg_latency_ms=150.0,
                success_rate=0.9,
                memory_usage_mb=512.0,
                total_time_seconds=0.15,
                individual_results=[],
            )

            result2 = BenchmarkResult(
                suite_name="suite2",
                model_backend="backend2",
                avg_tokens_per_second=70.0,
                avg_latency_ms=80.0,
                success_rate=1.0,
                memory_usage_mb=1024.0,
                total_time_seconds=0.08,
                individual_results=[],
            )

            results = {"suite1": [result1], "suite2": [result2]}

            report = tool.generate_report(results)

            # Check overall summary calculations
            assert "Average Tokens/Second: 50.00" in report  # (30+70)/2
            assert "Average Latency: 115.0ms" in report  # (150+80)/2
            assert "Overall Success Rate: 95.0%" in report  # (0.9+1.0)/2

            # Check individual suite sections
            assert "SUITE: SUITE1" in report
            assert "SUITE: SUITE2" in report

    @pytest.mark.asyncio
    async def test_run_benchmark_cli_integration(self):
        """Test the CLI integration function."""
        with TemporaryDirectory() as temp_dir:
            # Mock sys.argv for argparse
            test_args = [
                "benchmark_tool.py",
                "--output-dir",
                str(temp_dir),
                "--suites",
                "quick_qa",
            ]

            mock_infra = Mock(spec=AdaptiveLLMInfrastructure)
            mock_infra.startup = AsyncMock()
            mock_infra.shutdown = AsyncMock()

            # Mock the tool creation and benchmark execution
            with (
                patch("sys.argv", test_args),
                patch(
                    "entity.infrastructure.benchmark_tool.AdaptiveLLMInfrastructure",
                    return_value=mock_infra,
                ),
                patch(
                    "entity.infrastructure.benchmark_tool.LLMBenchmarkTool"
                ) as mock_tool_class,
            ):
                mock_tool = Mock()
                mock_tool.benchmark_suites = []
                mock_tool.output_dir = Path(temp_dir)
                mock_tool.run_comprehensive_benchmark = AsyncMock(return_value={})
                mock_tool.generate_report = Mock(return_value="Test Report")
                mock_tool_class.return_value = mock_tool

                # Should not raise any exceptions
                await run_benchmark_cli()

                mock_infra.startup.assert_called_once()
                mock_infra.shutdown.assert_called_once()
                mock_tool.run_comprehensive_benchmark.assert_called_once_with(
                    mock_infra
                )

    def test_benchmark_suite_filtering(self):
        """Test benchmark suite filtering by name."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            # Filter to only quick_qa suite
            original_count = len(tool.benchmark_suites)
            tool.benchmark_suites = [
                s for s in tool.benchmark_suites if s.name == "quick_qa"
            ]

            assert len(tool.benchmark_suites) == 1
            assert tool.benchmark_suites[0].name == "quick_qa"
            assert len(tool.benchmark_suites) < original_count

    def test_prompts_in_default_suites(self):
        """Test that default suites contain appropriate prompts."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            # Test quick_qa suite
            quick_qa = next(s for s in tool.benchmark_suites if s.name == "quick_qa")
            assert any("capital of France" in prompt for prompt in quick_qa.prompts)
            assert any("photosynthesis" in prompt for prompt in quick_qa.prompts)

            # Test reasoning_tasks suite
            reasoning = next(
                s for s in tool.benchmark_suites if s.name == "reasoning_tasks"
            )
            assert any("train" in prompt.lower() for prompt in reasoning.prompts)
            assert any("jug" in prompt for prompt in reasoning.prompts)

            # Test code_generation suite
            code_gen = next(
                s for s in tool.benchmark_suites if s.name == "code_generation"
            )
            assert any("Python" in prompt for prompt in code_gen.prompts)
            assert any("function" in prompt for prompt in code_gen.prompts)

            # Test creative_writing suite
            creative = next(
                s for s in tool.benchmark_suites if s.name == "creative_writing"
            )
            assert any("story" in prompt for prompt in creative.prompts)
            assert any("robot" in prompt for prompt in creative.prompts)

    @pytest.mark.asyncio
    async def test_benchmark_result_aggregation(self):
        """Test proper aggregation of individual benchmark results."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            suite = BenchmarkSuite(
                name="test_suite", prompts=["prompt1"], repetitions=3
            )

            mock_infra = Mock(spec=AdaptiveLLMInfrastructure)
            mock_infra.get_current_config.return_value = {"backend": "test_backend"}

            # Create varied benchmark results
            results = [
                PerformanceBenchmark(
                    tokens_per_second=40.0,
                    latency_ms=120.0,
                    memory_usage_mb=1000.0,
                    success=True,
                ),
                PerformanceBenchmark(
                    tokens_per_second=50.0,
                    latency_ms=100.0,
                    memory_usage_mb=1024.0,
                    success=True,
                ),
                PerformanceBenchmark(
                    tokens_per_second=60.0,
                    latency_ms=80.0,
                    memory_usage_mb=1048.0,
                    success=True,
                ),
            ]

            with patch.object(tool, "_run_single_benchmark", side_effect=results):
                suite_results = await tool._run_suite_benchmark(mock_infra, suite)

                assert len(suite_results) == 1
                result = suite_results[0]

                # Check aggregated values
                assert result.avg_tokens_per_second == 50.0  # (40+50+60)/3
                assert result.avg_latency_ms == 100.0  # (120+100+80)/3
                assert result.memory_usage_mb == 1024.0  # (1000+1024+1048)/3
                assert result.success_rate == 1.0  # All successful
                assert len(result.individual_results) == 3

    @pytest.mark.asyncio
    async def test_benchmark_partial_failures(self):
        """Test handling of partial failures in benchmark runs."""
        with TemporaryDirectory() as temp_dir:
            tool = LLMBenchmarkTool(output_dir=Path(temp_dir))

            suite = BenchmarkSuite(
                name="test_suite", prompts=["prompt1"], repetitions=3
            )

            mock_infra = Mock(spec=AdaptiveLLMInfrastructure)
            mock_infra.get_current_config.return_value = {"backend": "test_backend"}

            # Mix of successful and failed results
            def side_effect(*args, **kwargs):
                if not hasattr(side_effect, "call_count"):
                    side_effect.call_count = 0
                side_effect.call_count += 1

                if side_effect.call_count <= 2:
                    return PerformanceBenchmark(
                        tokens_per_second=50.0,
                        latency_ms=100.0,
                        memory_usage_mb=1024.0,
                        success=True,
                    )
                else:
                    raise Exception("Simulated failure")

            with patch.object(tool, "_run_single_benchmark", side_effect=side_effect):
                suite_results = await tool._run_suite_benchmark(mock_infra, suite)

                assert len(suite_results) == 1
                result = suite_results[0]

                # Should aggregate only successful results
                assert result.avg_tokens_per_second == 50.0  # Average of 2 successful
                assert result.success_rate == 2.0 / 3.0  # 2 out of 3 successful
                assert len(result.individual_results) == 3  # All attempts recorded
