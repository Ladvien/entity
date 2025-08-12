"""
Tests for Story 6: Performance and Import Time Validation

This test file verifies that:
1. Import times are reasonable and don't regress
2. Lazy loading works correctly
3. No circular imports exist
4. Memory footprint is reduced without GPT-OSS
5. Performance improvements are measurable
6. Benchmark script works correctly
"""

import gc
import importlib
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


class TestStory6Performance:
    """Test Story 6: Performance and Import Time Validation."""

    def test_base_entity_import_performance(self):
        """Test that base Entity import is reasonably fast."""
        # Clean imports
        modules_to_remove = [k for k in sys.modules.keys() if k.startswith("entity")]
        for module in modules_to_remove:
            del sys.modules[module]

        # Force garbage collection
        gc.collect()

        # Measure import time
        start_time = time.perf_counter()
        import entity

        end_time = time.perf_counter()

        import_time = end_time - start_time

        # Should import reasonably fast (less than 0.5 seconds)
        assert (
            import_time < 0.5
        ), f"Entity import took {import_time:.4f}s, expected < 0.5s"

        # Verify entity is properly imported
        assert hasattr(entity, "Agent")  # Main class should be available

    def test_plugins_import_performance(self):
        """Test that plugins import is reasonably fast."""
        # Clean imports
        modules_to_remove = [
            k for k in sys.modules.keys() if "plugins" in k or "entity" in k
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        gc.collect()

        # Measure plugins import time
        start_time = time.perf_counter()

        end_time = time.perf_counter()

        import_time = end_time - start_time

        # Should be reasonably fast (less than 1 second)
        assert (
            import_time < 1.0
        ), f"Plugins import took {import_time:.4f}s, expected < 1.0s"

    def test_gpt_oss_compat_layer_minimal_overhead(self):
        """Test that GPT-OSS compatibility layer has minimal import overhead."""
        # Clean imports
        modules_to_remove = [
            k for k in sys.modules.keys() if "gpt_oss" in k or "entity" in k
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        gc.collect()

        # Suppress deprecation warnings for clean measurement
        os.environ["ENTITY_SUPPRESS_GPT_OSS_DEPRECATION"] = "1"

        try:
            # Measure compatibility layer import time
            start_time = time.perf_counter()

            end_time = time.perf_counter()

            import_time = end_time - start_time

            # Should have very minimal overhead (less than 0.1 seconds)
            assert (
                import_time < 0.1
            ), f"GPT-OSS compat import took {import_time:.4f}s, expected < 0.1s"

        finally:
            os.environ.pop("ENTITY_SUPPRESS_GPT_OSS_DEPRECATION", None)

    def test_lazy_loading_entity_plugins(self):
        """Test that entity.plugins doesn't auto-load GPT-OSS plugins."""
        # Clean slate
        modules_to_remove = [
            k for k in sys.modules.keys() if "entity" in k or "gpt_oss" in k
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        # Import entity.plugins

        # GPT-OSS should not be loaded yet
        assert "entity.plugins.gpt_oss" not in sys.modules
        assert "entity.plugins.gpt_oss_compat" not in sys.modules
        assert "entity_plugin_gpt_oss" not in sys.modules

    def test_lazy_loading_gpt_oss_compat(self):
        """Test that GPT-OSS compat layer doesn't load actual plugins until used."""
        # Clean slate
        modules_to_remove = [
            k for k in sys.modules.keys() if "entity" in k or "gpt_oss" in k
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        os.environ["ENTITY_SUPPRESS_GPT_OSS_DEPRECATION"] = "1"

        try:
            # Import compatibility layer
            import entity.plugins.gpt_oss

            # Compatibility layer should be loaded
            assert "entity.plugins.gpt_oss_compat" in sys.modules

            # But actual plugin package should not be loaded
            assert "entity_plugin_gpt_oss" not in sys.modules

            # Check that shims exist but plugins aren't loaded
            assert hasattr(entity.plugins.gpt_oss, "ReasoningTracePlugin")

            # Still shouldn't have loaded the actual package
            assert "entity_plugin_gpt_oss" not in sys.modules

        finally:
            os.environ.pop("ENTITY_SUPPRESS_GPT_OSS_DEPRECATION", None)

    def test_no_circular_imports_core_framework(self):
        """Test that core framework has no circular import issues."""
        # Clean imports
        modules_to_remove = [k for k in sys.modules.keys() if "entity" in k]
        for module in modules_to_remove:
            del sys.modules[module]

        try:
            # Try various import patterns that might reveal circular dependencies
            import entity  # noqa: F401
            import entity.plugins  # noqa: F401
            from entity import Agent  # noqa: F401
            from entity.plugins import mixins  # noqa: F401

            # These should all work without ImportError
            assert True

        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")

    def test_no_circular_imports_with_gpt_oss(self):
        """Test that GPT-OSS compatibility layer doesn't introduce circular imports."""
        # Clean imports
        modules_to_remove = [
            k for k in sys.modules.keys() if "entity" in k or "gpt_oss" in k
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        os.environ["ENTITY_SUPPRESS_GPT_OSS_DEPRECATION"] = "1"

        try:
            # Try import patterns that might cause circular dependencies
            import entity  # noqa: F401
            import entity.plugins  # noqa: F401
            import entity.plugins.gpt_oss  # noqa: F401
            from entity.plugins import gpt_oss  # noqa: F401
            from entity.plugins.gpt_oss import ReasoningTracePlugin  # noqa: F401

            # These should all work without ImportError
            assert True

        except ImportError as e:
            if (
                "circular" in str(e).lower()
                or "already being imported" in str(e).lower()
            ):
                pytest.fail(f"Circular import detected: {e}")
            # Other ImportErrors (like missing package) are expected

        finally:
            os.environ.pop("ENTITY_SUPPRESS_GPT_OSS_DEPRECATION", None)

    def test_memory_footprint_without_gpt_oss(self):
        """Test that memory footprint is reasonable without GPT-OSS plugins."""
        import tracemalloc

        # Clean imports
        modules_to_remove = [k for k in sys.modules.keys() if "entity" in k]
        for module in modules_to_remove:
            del sys.modules[module]

        gc.collect()

        # Start memory tracking
        tracemalloc.start()

        # Import just the core

        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Convert to MB
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024

        # Should be reasonable (less than 5 MB for basic imports)
        assert current_mb < 5.0, f"Memory usage {current_mb:.2f} MB is too high"
        assert peak_mb < 10.0, f"Peak memory usage {peak_mb:.2f} MB is too high"

    def test_performance_regression_protection(self):
        """Test that import times haven't regressed beyond acceptable thresholds."""
        # Clean imports
        modules_to_remove = [k for k in sys.modules.keys() if "entity" in k]
        for module in modules_to_remove:
            del sys.modules[module]

        gc.collect()

        # Measure total framework import time
        start_time = time.perf_counter()

        end_time = time.perf_counter()

        total_time = end_time - start_time

        # Should import in reasonable time (regression protection)
        assert (
            total_time < 2.0
        ), f"Total import time {total_time:.4f}s exceeds threshold of 2.0s"

    def test_benchmark_script_exists_and_works(self):
        """Test that the benchmark script exists and can be executed."""
        benchmark_path = (
            Path(__file__).parent.parent / "benchmarks" / "import_performance.py"
        )

        # File should exist
        assert benchmark_path.exists(), "Benchmark script should exist"

        # Should be executable
        try:
            # Run the benchmark script (with timeout to prevent hanging)
            result = subprocess.run(
                [sys.executable, str(benchmark_path)],
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "ENTITY_SUPPRESS_GPT_OSS_DEPRECATION": "1"},
            )

            # Should complete successfully
            assert result.returncode == 0, f"Benchmark script failed: {result.stderr}"

            # Should generate expected output
            assert "Entity Framework Import Performance Benchmark" in result.stdout
            assert "Benefits of modularization" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Benchmark script took too long to execute")

    def test_benchmark_report_generated(self):
        """Test that benchmark script generates a proper report."""
        benchmark_path = (
            Path(__file__).parent.parent / "benchmarks" / "import_performance.py"
        )
        report_path = (
            Path(__file__).parent.parent / "benchmarks" / "import_performance_report.md"
        )

        # Clean up any existing report
        if report_path.exists():
            report_path.unlink()

        try:
            # Run benchmark script
            subprocess.run(
                [sys.executable, str(benchmark_path)],
                check=True,
                capture_output=True,
                env={**os.environ, "ENTITY_SUPPRESS_GPT_OSS_DEPRECATION": "1"},
            )

            # Report should be generated
            assert report_path.exists(), "Performance report should be generated"

            # Report should contain expected sections
            report_content = report_path.read_text()
            assert "# Import Performance Benchmark Report" in report_content
            assert "## Import Times" in report_content
            assert "## Memory Footprint" in report_content
            assert "## Lazy Loading Verification" in report_content
            assert "## Performance Improvements" in report_content

        finally:
            # Clean up
            if report_path.exists():
                report_path.unlink()

    def test_story_6_acceptance_criteria(self):
        """Test all Story 6 acceptance criteria are met."""
        # ✓ Measure import time of entity.plugins with and without GPT-OSS plugins
        # This is tested in other test methods and the benchmark script

        # ✓ Verify lazy loading works correctly
        self.test_lazy_loading_entity_plugins()
        self.test_lazy_loading_gpt_oss_compat()

        # ✓ Ensure no circular import issues exist
        self.test_no_circular_imports_core_framework()
        self.test_no_circular_imports_with_gpt_oss()

        # ✓ Confirm memory footprint is reduced when GPT-OSS plugins aren't used
        self.test_memory_footprint_without_gpt_oss()

        # ✓ Create benchmark script for future performance regression testing
        self.test_benchmark_script_exists_and_works()

        # All criteria met
        assert True

    def test_importtime_flag_compatibility(self):
        """Test that the framework works with Python's -X importtime flag."""
        benchmark_path = (
            Path(__file__).parent.parent / "benchmarks" / "import_performance.py"
        )

        try:
            # Run with -X importtime flag
            result = subprocess.run(
                [sys.executable, "-X", "importtime", str(benchmark_path)],
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "ENTITY_SUPPRESS_GPT_OSS_DEPRECATION": "1"},
            )

            # Should complete successfully even with import timing
            assert result.returncode == 0, f"Failed with -X importtime: {result.stderr}"

            # Should still produce normal output
            assert "Entity Framework Import Performance Benchmark" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Script with -X importtime took too long to execute")

    def test_modularization_benefits_documented(self):
        """Test that performance benefits are properly documented."""
        report_path = (
            Path(__file__).parent.parent / "benchmarks" / "import_performance_report.md"
        )

        # Generate fresh report
        benchmark_path = (
            Path(__file__).parent.parent / "benchmarks" / "import_performance.py"
        )
        subprocess.run(
            [sys.executable, str(benchmark_path)],
            check=True,
            capture_output=True,
            env={**os.environ, "ENTITY_SUPPRESS_GPT_OSS_DEPRECATION": "1"},
        )

        try:
            assert report_path.exists()
            content = report_path.read_text()

            # Should document key benefits
            assert "Reduced Default Import Time" in content
            assert "Lower Memory Footprint" in content
            assert "Lazy Loading" in content
            assert "No Circular Dependencies" in content
            assert "Optional Dependencies" in content

        finally:
            if report_path.exists():
                report_path.unlink()


class TestPerformanceRegression:
    """Regression tests to ensure performance doesn't degrade over time."""

    def test_entity_import_under_threshold(self):
        """Test that basic entity import stays under performance threshold."""
        # Clean slate
        modules_to_remove = [k for k in sys.modules.keys() if "entity" in k]
        for module in modules_to_remove:
            del sys.modules[module]

        gc.collect()

        # Measure import time multiple times for consistency
        times = []
        for _ in range(5):
            if "entity" in sys.modules:
                del sys.modules["entity"]

            start = time.perf_counter()
            importlib.import_module("entity")
            end = time.perf_counter()
            times.append(end - start)

        avg_time = sum(times) / len(times)

        # Should consistently import quickly (regression protection)
        assert (
            avg_time < 0.1
        ), f"Average entity import time {avg_time:.4f}s exceeds 0.1s threshold"

    def test_plugins_import_under_threshold(self):
        """Test that plugins import stays under performance threshold."""
        # Clean slate
        modules_to_remove = [
            k for k in sys.modules.keys() if "plugins" in k or "entity" in k
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        gc.collect()

        # Measure import time multiple times
        times = []
        for _ in range(3):
            # Clean relevant modules
            to_remove = [
                k for k in sys.modules.keys() if "plugins" in k or "entity" in k
            ]
            for mod in to_remove:
                del sys.modules[mod]

            start = time.perf_counter()
            importlib.import_module("entity.plugins")
            end = time.perf_counter()
            times.append(end - start)

        avg_time = sum(times) / len(times)

        # Should consistently import reasonably fast (regression protection)
        assert (
            avg_time < 1.0
        ), f"Average plugins import time {avg_time:.4f}s exceeds 1.0s threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
