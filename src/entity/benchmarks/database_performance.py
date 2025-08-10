"""Performance benchmarks comparing sync vs async database operations."""

import asyncio
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

from entity.infrastructure.async_duckdb_infra import AsyncDuckDBInfrastructure
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.resources.async_database import AsyncDatabaseResource
from entity.resources.async_memory import AsyncMemory
from entity.resources.database import DatabaseResource
from entity.resources.memory import Memory
from entity.resources.vector_store import VectorStoreResource


class DatabaseBenchmark:
    """Benchmark suite for comparing sync vs async database performance."""

    def __init__(self, num_operations: int = 1000):
        """Initialize benchmark with specified number of operations.

        Args:
            num_operations: Number of database operations to perform in each test
        """
        self.num_operations = num_operations
        self.results: Dict[str, Any] = {}

    async def setup_async_infrastructure(
        self, db_path: str
    ) -> tuple[AsyncMemory, AsyncDatabaseResource]:
        """Setup async database infrastructure for testing."""
        # Create async infrastructure
        async_infra = AsyncDuckDBInfrastructure(
            file_path=db_path, pool_size=10, query_timeout=30.0
        )
        await async_infra.startup()

        # Create async resources
        async_db = AsyncDatabaseResource(async_infra)
        vector_store = VectorStoreResource(
            async_infra
        )  # Use sync vector store for compatibility
        async_memory = AsyncMemory(async_db, vector_store)

        return async_memory, async_db

    def setup_sync_infrastructure(
        self, db_path: str
    ) -> tuple[Memory, DatabaseResource]:
        """Setup sync database infrastructure for testing."""
        # Create sync infrastructure
        sync_infra = DuckDBInfrastructure(file_path=db_path, pool_size=10)

        # Create sync resources
        sync_db = DatabaseResource(sync_infra)
        vector_store = VectorStoreResource(sync_infra)
        sync_memory = Memory(sync_db, vector_store)

        return sync_memory, sync_db

    async def benchmark_memory_operations(self) -> None:
        """Benchmark memory store/load operations comparing sync vs async."""
        print("🔍 Benchmarking Memory Operations...")

        with tempfile.TemporaryDirectory() as temp_dir:
            async_db_path = Path(temp_dir) / "async_test.db"
            sync_db_path = Path(temp_dir) / "sync_test.db"

            # Setup infrastructures
            async_memory, _ = await self.setup_async_infrastructure(str(async_db_path))
            sync_memory, _ = self.setup_sync_infrastructure(str(sync_db_path))

            # Prepare test data
            test_data = {
                f"key_{i}": {"id": i, "data": f"test_value_{i}", "nested": {"count": i}}
                for i in range(self.num_operations)
            }

            # Benchmark async memory operations
            start_time = time.perf_counter()
            for key, value in test_data.items():
                await async_memory.store(key, value)
            async_store_time = time.perf_counter() - start_time

            start_time = time.perf_counter()
            async_loaded_data = {}
            for key in test_data.keys():
                async_loaded_data[key] = await async_memory.load(key)
            async_load_time = time.perf_counter() - start_time

            # Benchmark sync memory operations (with async wrapper)
            start_time = time.perf_counter()
            for key, value in test_data.items():
                await sync_memory.store(key, value)
            sync_store_time = time.perf_counter() - start_time

            start_time = time.perf_counter()
            sync_loaded_data = {}
            for key in test_data.keys():
                sync_loaded_data[key] = await sync_memory.load(key)
            sync_load_time = time.perf_counter() - start_time

            # Benchmark batch operations (async only)
            start_time = time.perf_counter()
            await async_memory.batch_store(test_data)
            batch_store_time = time.perf_counter() - start_time

            start_time = time.perf_counter()
            batch_loaded_data = await async_memory.batch_load(list(test_data.keys()))
            batch_load_time = time.perf_counter() - start_time

            # Store results
            self.results["memory_operations"] = {
                "num_operations": self.num_operations,
                "async_store_time": async_store_time,
                "async_load_time": async_load_time,
                "async_total_time": async_store_time + async_load_time,
                "sync_store_time": sync_store_time,
                "sync_load_time": sync_load_time,
                "sync_total_time": sync_store_time + sync_load_time,
                "batch_store_time": batch_store_time,
                "batch_load_time": batch_load_time,
                "batch_total_time": batch_store_time + batch_load_time,
                "async_ops_per_second": self.num_operations
                * 2
                / (async_store_time + async_load_time),
                "sync_ops_per_second": self.num_operations
                * 2
                / (sync_store_time + sync_load_time),
                "batch_ops_per_second": self.num_operations
                * 2
                / (batch_store_time + batch_load_time),
                "performance_improvement": (sync_store_time + sync_load_time)
                / (async_store_time + async_load_time),
                "batch_improvement": (async_store_time + async_load_time)
                / (batch_store_time + batch_load_time),
            }

            # Verify data integrity
            assert len(async_loaded_data) == len(test_data)
            assert len(sync_loaded_data) == len(test_data)
            assert len(batch_loaded_data) == len(test_data)

            # Cleanup
            await async_memory.database.infrastructure.shutdown()

    async def benchmark_raw_database_operations(self) -> None:
        """Benchmark raw database operations comparing sync vs async."""
        print("🔍 Benchmarking Raw Database Operations...")

        with tempfile.TemporaryDirectory() as temp_dir:
            async_db_path = Path(temp_dir) / "async_db_test.db"
            sync_db_path = Path(temp_dir) / "sync_db_test.db"

            # Setup infrastructures
            _, async_db = await self.setup_async_infrastructure(str(async_db_path))
            _, sync_db = self.setup_sync_infrastructure(str(sync_db_path))

            # Create test tables
            await async_db.execute(
                """
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value REAL,
                    data TEXT
                )
            """
            )

            await asyncio.to_thread(
                sync_db.execute,
                """
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value REAL,
                    data TEXT
                )
            """,
            )

            # Prepare test data
            test_records = [
                (i, f"name_{i}", i * 1.5, f"data_string_{i}")
                for i in range(self.num_operations)
            ]

            # Benchmark async database inserts
            start_time = time.perf_counter()
            for record in test_records:
                await async_db.execute(
                    "INSERT INTO test_table (id, name, value, data) VALUES (?, ?, ?, ?)",
                    *record,
                )
            async_insert_time = time.perf_counter() - start_time

            # Benchmark sync database inserts
            start_time = time.perf_counter()
            for record in test_records:
                await asyncio.to_thread(
                    sync_db.execute,
                    "INSERT INTO test_table (id, name, value, data) VALUES (?, ?, ?, ?)",
                    *record,
                )
            sync_insert_time = time.perf_counter() - start_time

            # Benchmark batch inserts (async only)
            await async_db.execute("DELETE FROM test_table")  # Clear for batch test

            start_time = time.perf_counter()
            await async_db.execute_many(
                "INSERT INTO test_table (id, name, value, data) VALUES (?, ?, ?, ?)",
                test_records,
            )
            batch_insert_time = time.perf_counter() - start_time

            # Benchmark selects
            start_time = time.perf_counter()
            for i in range(
                min(100, self.num_operations)
            ):  # Select subset for performance
                await async_db.execute_fetch_one(
                    "SELECT * FROM test_table WHERE id = ?", i
                )
            async_select_time = time.perf_counter() - start_time

            start_time = time.perf_counter()
            for i in range(min(100, self.num_operations)):
                await asyncio.to_thread(
                    sync_db.execute, "SELECT * FROM test_table WHERE id = ?", i
                )
            sync_select_time = time.perf_counter() - start_time

            # Store results
            self.results["database_operations"] = {
                "num_operations": self.num_operations,
                "async_insert_time": async_insert_time,
                "sync_insert_time": sync_insert_time,
                "batch_insert_time": batch_insert_time,
                "async_select_time": async_select_time,
                "sync_select_time": sync_select_time,
                "async_insert_ops_per_second": self.num_operations / async_insert_time,
                "sync_insert_ops_per_second": self.num_operations / sync_insert_time,
                "batch_insert_ops_per_second": self.num_operations / batch_insert_time,
                "insert_performance_improvement": sync_insert_time / async_insert_time,
                "batch_performance_improvement": async_insert_time / batch_insert_time,
                "select_performance_improvement": sync_select_time / async_select_time,
            }

            # Cleanup
            await async_db.infrastructure.shutdown()

    async def benchmark_concurrent_operations(self) -> None:
        """Benchmark concurrent database operations to test connection pooling."""
        print("🔍 Benchmarking Concurrent Operations...")

        with tempfile.TemporaryDirectory() as temp_dir:
            async_db_path = Path(temp_dir) / "async_concurrent_test.db"

            # Setup async infrastructure with larger pool
            async_infra = AsyncDuckDBInfrastructure(
                file_path=str(async_db_path), pool_size=20, query_timeout=30.0
            )
            await async_infra.startup()
            async_db = AsyncDatabaseResource(async_infra)

            # Create test table
            await async_db.execute(
                """
                CREATE TABLE IF NOT EXISTS concurrent_test (
                    id INTEGER PRIMARY KEY,
                    thread_id INTEGER,
                    data TEXT
                )
            """
            )

            async def worker_task(worker_id: int, operations_per_worker: int):
                """Worker task for concurrent testing."""
                for i in range(operations_per_worker):
                    # Insert operation
                    await async_db.execute(
                        "INSERT INTO concurrent_test (thread_id, data) VALUES (?, ?)",
                        worker_id,
                        f"data_from_worker_{worker_id}_op_{i}",
                    )

                    # Select operation
                    await async_db.execute_fetch_all(
                        "SELECT * FROM concurrent_test WHERE thread_id = ? LIMIT 10",
                        worker_id,
                    )

            # Test different concurrency levels
            concurrency_levels = [1, 5, 10, 20]
            results = {}

            for concurrency in concurrency_levels:
                operations_per_worker = max(1, self.num_operations // concurrency)

                # Clear table
                await async_db.execute("DELETE FROM concurrent_test")

                # Run concurrent operations
                start_time = time.perf_counter()
                tasks = [
                    worker_task(worker_id, operations_per_worker)
                    for worker_id in range(concurrency)
                ]
                await asyncio.gather(*tasks)
                total_time = time.perf_counter() - start_time

                total_operations = (
                    concurrency * operations_per_worker * 2
                )  # Insert + Select
                ops_per_second = total_operations / total_time

                results[f"concurrency_{concurrency}"] = {
                    "concurrency_level": concurrency,
                    "operations_per_worker": operations_per_worker,
                    "total_operations": total_operations,
                    "total_time": total_time,
                    "ops_per_second": ops_per_second,
                }

            self.results["concurrent_operations"] = results

            # Get connection stats
            stats = await async_db.get_connection_stats()
            self.results["connection_stats"] = stats

            # Cleanup
            await async_infra.shutdown()

    def print_results(self) -> None:
        """Print formatted benchmark results."""
        print("\n" + "=" * 80)
        print("🚀 DATABASE PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)

        if "memory_operations" in self.results:
            mem = self.results["memory_operations"]
            print(f"\n📊 Memory Operations ({mem['num_operations']} ops):")
            print(f"  Async Total Time:     {mem['async_total_time']:.3f}s")
            print(f"  Sync Total Time:      {mem['sync_total_time']:.3f}s")
            print(f"  Batch Total Time:     {mem['batch_total_time']:.3f}s")
            print(f"  Async Ops/sec:        {mem['async_ops_per_second']:.1f}")
            print(f"  Sync Ops/sec:         {mem['sync_ops_per_second']:.1f}")
            print(f"  Batch Ops/sec:        {mem['batch_ops_per_second']:.1f}")
            print(f"  Performance Gain:     {mem['performance_improvement']:.2f}x")
            print(f"  Batch Improvement:    {mem['batch_improvement']:.2f}x")

        if "database_operations" in self.results:
            db = self.results["database_operations"]
            print(f"\n📊 Database Operations ({db['num_operations']} ops):")
            print(f"  Async Insert Time:    {db['async_insert_time']:.3f}s")
            print(f"  Sync Insert Time:     {db['sync_insert_time']:.3f}s")
            print(f"  Batch Insert Time:    {db['batch_insert_time']:.3f}s")
            print(
                f"  Insert Performance:   {db['insert_performance_improvement']:.2f}x"
            )
            print(f"  Batch Performance:    {db['batch_performance_improvement']:.2f}x")
            print(
                f"  Select Performance:   {db['select_performance_improvement']:.2f}x"
            )

        if "concurrent_operations" in self.results:
            print("\n📊 Concurrent Operations:")
            for level, data in self.results["concurrent_operations"].items():
                if isinstance(data, dict):
                    print(
                        f"  {data['concurrency_level']:2d} threads: "
                        f"{data['ops_per_second']:8.1f} ops/sec "
                        f"({data['total_time']:.3f}s total)"
                    )

        if "connection_stats" in self.results:
            stats = self.results["connection_stats"]
            print("\n📊 Connection Pool Stats:")
            print(f"  Pool Size:            {stats['pool_size']}")
            print(f"  Active Connections:   {stats['active_connections']}")
            print(f"  Query Timeout:        {stats['query_timeout']}s")

        print("\n" + "=" * 80)

    async def run_all_benchmarks(self) -> None:
        """Run all benchmark tests."""
        print(
            f"🏁 Starting Database Performance Benchmarks ({self.num_operations} operations)"
        )

        try:
            await self.benchmark_memory_operations()
            await self.benchmark_raw_database_operations()
            await self.benchmark_concurrent_operations()

            self.print_results()

        except Exception as e:
            print(f"❌ Benchmark failed: {e}")
            raise


async def main():
    """Main function to run benchmarks."""
    # Run benchmarks with different operation counts
    for num_ops in [100, 1000]:
        print(f"\n{'='*60}")
        print(f"Running benchmark with {num_ops} operations")
        print(f"{'='*60}")

        benchmark = DatabaseBenchmark(num_operations=num_ops)
        await benchmark.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())
