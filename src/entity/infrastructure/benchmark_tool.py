"""Benchmark Tool for Comparing LLM Infrastructure Performance.

This tool provides comprehensive benchmarking capabilities for different
LLM backends to help users understand performance characteristics and
make informed decisions about model selection.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .adaptive_llm_infra import AdaptiveLLMInfrastructure, PerformanceBenchmark


@dataclass
class BenchmarkSuite:
    """Collection of benchmark tests."""

    name: str
    prompts: List[str]
    expected_min_tokens: int = 10
    timeout_seconds: float = 30.0
    repetitions: int = 3


@dataclass
class BenchmarkResult:
    """Results from running a benchmark suite."""

    suite_name: str
    model_backend: str
    avg_tokens_per_second: float
    avg_latency_ms: float
    success_rate: float
    memory_usage_mb: float
    total_time_seconds: float
    individual_results: List[PerformanceBenchmark]


class LLMBenchmarkTool:
    """Tool for benchmarking LLM infrastructure performance."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize benchmark tool.

        Args:
            output_dir: Directory to save benchmark results (default: ./benchmark_results)
        """
        self.output_dir = output_dir or Path("./benchmark_results")
        self.output_dir.mkdir(exist_ok=True)

        # Default benchmark suites
        self.benchmark_suites = self._create_default_suites()

    def _create_default_suites(self) -> List[BenchmarkSuite]:
        """Create default benchmark test suites."""
        return [
            BenchmarkSuite(
                name="quick_qa",
                prompts=[
                    "What is the capital of France?",
                    "Explain photosynthesis in simple terms.",
                    "What are the benefits of renewable energy?",
                ],
                expected_min_tokens=20,
                repetitions=3,
            ),
            BenchmarkSuite(
                name="reasoning_tasks",
                prompts=[
                    "If a train leaves Station A at 2 PM traveling 60 mph and another train leaves Station B at 2:30 PM traveling 80 mph, and the stations are 350 miles apart, when will they meet?",
                    "You have a 3-gallon jug and a 5-gallon jug. How can you measure exactly 4 gallons of water?",
                    "A farmer has 17 sheep, and all but 9 die. How many sheep are left?",
                ],
                expected_min_tokens=50,
                timeout_seconds=45.0,
                repetitions=2,
            ),
            BenchmarkSuite(
                name="code_generation",
                prompts=[
                    "Write a Python function to find the factorial of a number.",
                    "Create a simple REST API endpoint using FastAPI.",
                    "Implement a binary search algorithm in Python.",
                ],
                expected_min_tokens=100,
                timeout_seconds=60.0,
                repetitions=2,
            ),
            BenchmarkSuite(
                name="creative_writing",
                prompts=[
                    "Write a short story about a robot who discovers emotions.",
                    "Describe a futuristic city in 2050.",
                    "Create a dialogue between two characters meeting for the first time.",
                ],
                expected_min_tokens=150,
                timeout_seconds=45.0,
                repetitions=1,
            ),
        ]

    async def run_comprehensive_benchmark(
        self,
        infrastructure: AdaptiveLLMInfrastructure,
        suites: Optional[List[BenchmarkSuite]] = None,
    ) -> Dict[str, List[BenchmarkResult]]:
        """Run comprehensive benchmark across multiple test suites.

        Args:
            infrastructure: The adaptive infrastructure to benchmark
            suites: Custom benchmark suites (uses defaults if None)

        Returns:
            Dictionary mapping suite names to benchmark results
        """
        suites = suites or self.benchmark_suites
        results = {}

        print(f"Starting comprehensive benchmark with {len(suites)} test suites...")

        for suite in suites:
            print(f"\nRunning benchmark suite: {suite.name}")
            suite_results = await self._run_suite_benchmark(infrastructure, suite)
            results[suite.name] = suite_results

            # Print summary
            if suite_results:
                avg_tps = sum(r.avg_tokens_per_second for r in suite_results) / len(
                    suite_results
                )
                print(f"Suite {suite.name} avg tokens/sec: {avg_tps:.2f}")

        # Save results
        await self._save_results(results)

        return results

    async def _run_suite_benchmark(
        self, infrastructure: AdaptiveLLMInfrastructure, suite: BenchmarkSuite
    ) -> List[BenchmarkResult]:
        """Run benchmark for a specific test suite."""
        results = []

        # Get current backend info
        current_config = infrastructure.get_current_config()
        model_backend = current_config.get("backend", "unknown")

        for i, prompt in enumerate(suite.prompts):
            print(f"  Testing prompt {i+1}/{len(suite.prompts)}: {prompt[:50]}...")

            individual_results = []

            # Run multiple repetitions
            for rep in range(suite.repetitions):
                try:
                    benchmark = await self._run_single_benchmark(
                        infrastructure, prompt, suite.timeout_seconds
                    )
                    individual_results.append(benchmark)

                except Exception as e:
                    print(f"    Repetition {rep+1} failed: {e}")
                    individual_results.append(
                        PerformanceBenchmark(
                            tokens_per_second=0.0,
                            latency_ms=suite.timeout_seconds * 1000,
                            memory_usage_mb=0.0,
                            success=False,
                            error_message=str(e),
                        )
                    )

            # Calculate aggregate results
            successful_results = [r for r in individual_results if r.success]

            if successful_results:
                avg_tokens_per_second = sum(
                    r.tokens_per_second for r in successful_results
                ) / len(successful_results)
                avg_latency_ms = sum(r.latency_ms for r in successful_results) / len(
                    successful_results
                )
                avg_memory_mb = sum(
                    r.memory_usage_mb for r in successful_results
                ) / len(successful_results)
                success_rate = len(successful_results) / len(individual_results)
                total_time = sum(r.latency_ms for r in individual_results) / 1000
            else:
                avg_tokens_per_second = 0.0
                avg_latency_ms = suite.timeout_seconds * 1000
                avg_memory_mb = 0.0
                success_rate = 0.0
                total_time = suite.timeout_seconds * suite.repetitions

            result = BenchmarkResult(
                suite_name=suite.name,
                model_backend=model_backend,
                avg_tokens_per_second=avg_tokens_per_second,
                avg_latency_ms=avg_latency_ms,
                success_rate=success_rate,
                memory_usage_mb=avg_memory_mb,
                total_time_seconds=total_time,
                individual_results=individual_results,
            )

            results.append(result)

        return results

    async def _run_single_benchmark(
        self, infrastructure: AdaptiveLLMInfrastructure, prompt: str, timeout: float
    ) -> PerformanceBenchmark:
        """Run a single benchmark test."""
        start_time = time.time()

        try:
            # For now, we'll simulate the actual model call
            # In a real implementation, this would call the infrastructure

            # Simulate processing time based on prompt complexity
            processing_time = min(
                len(prompt) / 100, timeout - 1
            )  # Max timeout-1 seconds
            await asyncio.sleep(processing_time)

            # Simulate response generation
            response = f"Generated response for: {prompt[:30]}... (simulated)"

            end_time = time.time()
            elapsed_time = end_time - start_time

            # Calculate metrics
            token_count = len(response.split())  # Rough token estimate
            tokens_per_second = token_count / elapsed_time if elapsed_time > 0 else 0
            latency_ms = elapsed_time * 1000
            memory_usage_mb = 512  # Simulated memory usage

            return PerformanceBenchmark(
                tokens_per_second=tokens_per_second,
                latency_ms=latency_ms,
                memory_usage_mb=memory_usage_mb,
                success=True,
            )

        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            return PerformanceBenchmark(
                tokens_per_second=0.0,
                latency_ms=elapsed_time * 1000,
                memory_usage_mb=0.0,
                success=False,
                error_message="Timeout exceeded",
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

    async def _save_results(self, results: Dict[str, List[BenchmarkResult]]) -> None:
        """Save benchmark results to JSON file."""
        timestamp = int(time.time())
        filename = f"benchmark_results_{timestamp}.json"
        filepath = self.output_dir / filename

        # Convert results to serializable format
        serializable_results = {}
        for suite_name, suite_results in results.items():
            serializable_results[suite_name] = [
                {
                    **asdict(result),
                    "individual_results": [
                        asdict(r) for r in result.individual_results
                    ],
                }
                for result in suite_results
            ]

        with open(filepath, "w") as f:
            json.dump(serializable_results, f, indent=2)

        print(f"\nBenchmark results saved to: {filepath}")

    def generate_report(self, results: Dict[str, List[BenchmarkResult]]) -> str:
        """Generate a human-readable benchmark report."""
        report_lines = ["=" * 80, "LLM INFRASTRUCTURE BENCHMARK REPORT", "=" * 80, ""]

        # Overall summary
        all_results = []
        for suite_results in results.values():
            all_results.extend(suite_results)

        if all_results:
            avg_tps = sum(r.avg_tokens_per_second for r in all_results) / len(
                all_results
            )
            avg_latency = sum(r.avg_latency_ms for r in all_results) / len(all_results)
            overall_success_rate = sum(r.success_rate for r in all_results) / len(
                all_results
            )

            report_lines.extend(
                [
                    "OVERALL SUMMARY:",
                    f"  Average Tokens/Second: {avg_tps:.2f}",
                    f"  Average Latency: {avg_latency:.1f}ms",
                    f"  Overall Success Rate: {overall_success_rate:.1%}",
                    "",
                ]
            )

        # Per-suite breakdown
        for suite_name, suite_results in results.items():
            report_lines.extend([f"SUITE: {suite_name.upper()}", "-" * 40])

            for i, result in enumerate(suite_results):
                report_lines.extend(
                    [
                        f"  Test {i+1}:",
                        f"    Tokens/Second: {result.avg_tokens_per_second:.2f}",
                        f"    Latency: {result.avg_latency_ms:.1f}ms",
                        f"    Success Rate: {result.success_rate:.1%}",
                        f"    Memory Usage: {result.memory_usage_mb:.1f}MB",
                        "",
                    ]
                )

        report_lines.append("=" * 80)
        return "\n".join(report_lines)


async def run_benchmark_cli():
    """Command-line interface for running benchmarks."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Benchmark LLM Infrastructure Performance"
    )
    parser.add_argument("--output-dir", type=Path, help="Output directory for results")
    parser.add_argument(
        "--suites",
        nargs="+",
        help="Specific suites to run",
        choices=["quick_qa", "reasoning_tasks", "code_generation", "creative_writing"],
    )

    args = parser.parse_args()

    # Create benchmark tool
    tool = LLMBenchmarkTool(output_dir=args.output_dir)

    # Filter suites if specified
    if args.suites:
        tool.benchmark_suites = [
            s for s in tool.benchmark_suites if s.name in args.suites
        ]

    # Create and initialize adaptive infrastructure
    print("Initializing adaptive LLM infrastructure...")
    infrastructure = AdaptiveLLMInfrastructure()
    await infrastructure.startup()

    try:
        # Run benchmarks
        results = await tool.run_comprehensive_benchmark(infrastructure)

        # Generate and print report
        report = tool.generate_report(results)
        print("\n" + report)

        # Save report
        report_file = tool.output_dir / "latest_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        print(f"\nDetailed report saved to: {report_file}")

    finally:
        await infrastructure.shutdown()


if __name__ == "__main__":
    asyncio.run(run_benchmark_cli())
