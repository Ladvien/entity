"""Comprehensive tests for SecureDatabaseResource with SQL injection prevention."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.resources.secure_database import (
    QueryType,
    SecureDatabaseResource,
    SQLQueryValidator,
)


class TestSQLQueryValidator:
    """Test SQL query validation functionality."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return SQLQueryValidator(strict_mode=True)

    @pytest.fixture
    def lenient_validator(self):
        """Create a lenient validator instance."""
        return SQLQueryValidator(strict_mode=False)

    def test_validate_table_name_valid(self, validator):
        """Test validation of valid table names."""
        valid_names = [
            "users",
            "user_accounts",
            "schema.table",
            "my_schema.my_table",
            "_internal_table",
            "table123",
        ]

        for name in valid_names:
            assert validator.validate_table_name(name) is True

    def test_validate_table_name_invalid(self, validator):
        """Test validation of invalid table names."""
        invalid_names = [
            "",  # Empty
            "123table",  # Starts with number
            "table-name",  # Contains hyphen
            "table name",  # Contains space
            "DROP TABLE users",  # SQL injection attempt
            "users; DROP TABLE accounts",  # Multi-statement
            "users/*comment*/",  # Contains comment
            "users--comment",  # Contains comment
            "UNION SELECT * FROM passwords",  # UNION attack
        ]

        for name in invalid_names:
            assert validator.validate_table_name(name) is False

    def test_validate_column_names_valid(self, validator):
        """Test validation of valid column names."""
        valid_columns = ["id", "user_name", "created_at", "_internal", "column123"]

        is_valid, invalid = validator.validate_column_names(valid_columns)
        assert is_valid is True
        assert invalid == []

    def test_validate_column_names_invalid(self, validator):
        """Test validation of invalid column names."""
        invalid_columns = [
            "123column",  # Starts with number
            "column-name",  # Contains hyphen
            "column name",  # Contains space
            "DROP/**/COLUMN",  # Injection attempt
        ]

        is_valid, invalid = validator.validate_column_names(invalid_columns)
        assert is_valid is False
        assert len(invalid) == 4

    def test_validate_query_detects_injection_patterns(self, validator):
        """Test detection of SQL injection patterns."""
        injection_queries = [
            "SELECT * FROM users; DROP TABLE accounts",  # Multi-statement
            "SELECT * FROM users WHERE id = 1 OR 1=1",  # OR attack
            "SELECT * FROM users WHERE name = 'admin' OR 'a'='a'",  # String OR attack
            "SELECT * FROM users UNION SELECT * FROM passwords",  # UNION attack
            "SELECT * FROM users WHERE id = 1; -- comment",  # Comment injection
            "SELECT * FROM users /* comment */ WHERE id = 1",  # Block comment
            "SELECT * FROM users WHERE SLEEP(10)",  # Time-based attack
            "EXEC xp_cmdshell 'dir'",  # Command execution
            "SELECT LOAD_FILE('/etc/passwd')",  # File operation
        ]

        for query in injection_queries:
            is_valid, issues = validator.validate_query(query)
            assert is_valid is False
            assert len(issues) > 0

    def test_validate_query_allows_safe_queries(self, validator):
        """Test that safe queries pass validation."""
        safe_queries = [
            "SELECT * FROM users WHERE id = ?",
            "INSERT INTO users (name, email) VALUES (?, ?)",
            "UPDATE users SET name = ? WHERE id = ?",
            "DELETE FROM users WHERE id = ?",
        ]

        for query in safe_queries:
            is_valid, issues = validator.validate_query(query)
            assert is_valid is True
            assert issues == []

    def test_validate_query_strict_mode(self, validator):
        """Test strict mode query type validation."""
        # Should fail if query doesn't match expected type
        is_valid, issues = validator.validate_query(
            "INSERT INTO users VALUES (?)", QueryType.SELECT
        )
        assert is_valid is False
        assert any("does not start with expected SELECT" in issue for issue in issues)

        # Should pass if query matches expected type
        is_valid, issues = validator.validate_query(
            "SELECT * FROM users", QueryType.SELECT
        )
        assert is_valid is True

    def test_sanitize_identifier(self, validator):
        """Test identifier sanitization."""
        test_cases = [
            ("valid_name", "valid_name"),
            ("name-with-hyphen", "namewithhyphen"),
            ("name with spaces", "namewithspaces"),
            ("123name", "_123name"),  # Prepend underscore if starts with number
            ("name!@#$%", "name"),  # Remove special characters
            ("", ""),  # Empty string
        ]

        for input_val, expected in test_cases:
            assert validator.sanitize_identifier(input_val) == expected


class TestSecureDatabaseResource:
    """Test SecureDatabaseResource functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "test.db"

    @pytest.fixture
    def infrastructure(self, temp_db):
        """Create database infrastructure."""
        return DuckDBInfrastructure(str(temp_db))

    @pytest.fixture
    def secure_db(self, infrastructure):
        """Create SecureDatabaseResource instance."""
        return SecureDatabaseResource(
            infrastructure,
            enable_query_logging=True,
            max_audit_entries=100,
            strict_validation=True,
        )

    def test_initialization(self, secure_db):
        """Test proper initialization of SecureDatabaseResource."""
        assert secure_db._table_registry is not None
        assert secure_db._query_validator is not None
        assert secure_db._audit_log == []
        assert secure_db._enable_query_logging is True
        assert secure_db._max_audit_entries == 100

    def test_register_table_valid(self, secure_db):
        """Test registering valid tables."""
        secure_db.register_table("users", "user_accounts")
        assert secure_db._table_registry["users"] == "user_accounts"

        secure_db.register_table("products", "product_catalog")
        assert secure_db._table_registry["products"] == "product_catalog"

    def test_register_table_invalid(self, secure_db):
        """Test registering invalid tables."""
        # Invalid table name
        with pytest.raises(ValueError, match="Invalid table name"):
            secure_db.register_table("alias", "DROP TABLE users")

        # Invalid alias
        with pytest.raises(ValueError, match="Invalid table alias"):
            secure_db.register_table("123invalid", "valid_table")

        with pytest.raises(ValueError, match="Invalid table alias"):
            secure_db.register_table("", "valid_table")

    def test_unregister_table(self, secure_db):
        """Test unregistering tables."""
        secure_db.register_table("temp", "temp_table")
        assert "temp" in secure_db._table_registry

        secure_db.unregister_table("temp")
        assert "temp" not in secure_db._table_registry

        # Unregistering non-existent table should not raise
        secure_db.unregister_table("non_existent")

    def test_get_registered_tables(self, secure_db):
        """Test getting registered tables."""
        secure_db.register_table("table1", "actual_table1")
        secure_db.register_table("table2", "actual_table2")

        tables = secure_db.get_registered_tables()
        assert tables["table1"] == "actual_table1"
        assert tables["table2"] == "actual_table2"

        # Should return a copy, not reference
        tables["table3"] = "new_table"
        assert "table3" not in secure_db._table_registry

    def test_set_allowed_query_types(self, secure_db):
        """Test setting allowed query types."""
        secure_db.set_allowed_query_types([QueryType.SELECT, QueryType.INSERT])
        assert QueryType.SELECT in secure_db._allowed_query_types
        assert QueryType.INSERT in secure_db._allowed_query_types
        assert QueryType.DELETE not in secure_db._allowed_query_types

    def test_execute_safe_with_registered_table(self, secure_db):
        """Test safe execution with registered tables."""
        # Create a test table
        secure_db.execute("CREATE TABLE test_users (id INTEGER, name TEXT)")
        secure_db.register_table("users", "test_users")

        # Insert data safely
        secure_db.execute_safe(
            "INSERT INTO {table} VALUES (?, ?)",
            1,
            "Alice",
            table_alias="users",
            query_type=QueryType.INSERT,
        )

        # Select data safely
        result = secure_db.execute_safe(
            "SELECT * FROM {table} WHERE id = ?",
            1,
            table_alias="users",
            query_type=QueryType.SELECT,
        )

        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0] == (1, "Alice")

    def test_execute_safe_with_unregistered_table(self, secure_db):
        """Test that unregistered tables are rejected."""
        with pytest.raises(ValueError, match="Unregistered table alias"):
            secure_db.execute_safe(
                "SELECT * FROM {table}",
                table_alias="unregistered",
                query_type=QueryType.SELECT,
            )

    def test_execute_safe_with_injection_attempt(self, secure_db):
        """Test that injection attempts are blocked."""
        secure_db.register_table("users", "test_users")

        # Multi-statement injection
        with pytest.raises(ValueError, match="Query validation failed"):
            secure_db.execute_safe(
                "SELECT * FROM {table}; DROP TABLE accounts",
                table_alias="users",
                query_type=QueryType.SELECT,
            )

        # UNION injection
        with pytest.raises(ValueError, match="Query validation failed"):
            secure_db.execute_safe(
                "SELECT * FROM {table} UNION SELECT * FROM passwords",
                table_alias="users",
                query_type=QueryType.SELECT,
            )

    def test_execute_safe_with_disallowed_query_type(self, secure_db):
        """Test that disallowed query types are blocked."""
        secure_db.register_table("users", "test_users")
        secure_db.set_allowed_query_types([QueryType.SELECT])

        with pytest.raises(ValueError, match="Query type DELETE is not allowed"):
            secure_db.execute_safe(
                "DELETE FROM {table} WHERE id = ?",
                1,
                table_alias="users",
                query_type=QueryType.DELETE,
            )

    def test_execute_safe_select(self, secure_db):
        """Test safe SELECT execution."""
        # Create and populate test table
        secure_db.execute("CREATE TABLE test_users (id INTEGER, name TEXT, email TEXT)")
        secure_db.execute(
            "INSERT INTO test_users VALUES (1, 'Alice', 'alice@test.com')"
        )
        secure_db.execute("INSERT INTO test_users VALUES (2, 'Bob', 'bob@test.com')")
        secure_db.register_table("users", "test_users")

        # Select specific columns
        result = secure_db.execute_safe_select("users", ["id", "name"], "id = ?", 1)
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0] == (1, "Alice")

        # Select all columns
        result = secure_db.execute_safe_select("users", [], "")
        rows = result.fetchall()
        assert len(rows) == 2

    def test_execute_safe_select_invalid_columns(self, secure_db):
        """Test that invalid column names are rejected."""
        secure_db.register_table("users", "test_users")

        with pytest.raises(ValueError, match="Invalid column names"):
            secure_db.execute_safe_select(
                "users", ["id", "name; DROP TABLE"], "id = ?", 1
            )

    def test_execute_safe_insert(self, secure_db):
        """Test safe INSERT execution."""
        # Create test table
        secure_db.execute("CREATE TABLE test_users (id INTEGER, name TEXT, email TEXT)")
        secure_db.register_table("users", "test_users")

        # Insert data
        secure_db.execute_safe_insert(
            "users",
            {"id": 1, "name": "Alice", "email": "alice@test.com"},
        )

        # Verify insertion
        result = secure_db.execute("SELECT * FROM test_users")
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0] == (1, "Alice", "alice@test.com")

    def test_execute_safe_insert_invalid_columns(self, secure_db):
        """Test that invalid column names in INSERT are rejected."""
        secure_db.register_table("users", "test_users")

        with pytest.raises(ValueError, match="Invalid column names"):
            secure_db.execute_safe_insert(
                "users",
                {"id": 1, "name; DROP TABLE": "Alice"},
            )

    def test_execute_safe_update(self, secure_db):
        """Test safe UPDATE execution."""
        # Create and populate test table
        secure_db.execute("CREATE TABLE test_users (id INTEGER, name TEXT, email TEXT)")
        secure_db.execute("INSERT INTO test_users VALUES (1, 'Alice', 'alice@old.com')")
        secure_db.register_table("users", "test_users")

        # Update data
        secure_db.execute_safe_update(
            "users",
            {"email": "alice@new.com"},
            "id = ?",
            1,
        )

        # Verify update
        result = secure_db.execute("SELECT email FROM test_users WHERE id = 1")
        email = result.fetchone()[0]
        assert email == "alice@new.com"

    def test_execute_safe_delete(self, secure_db):
        """Test safe DELETE execution."""
        # Create and populate test table
        secure_db.execute("CREATE TABLE test_users (id INTEGER, name TEXT)")
        secure_db.execute("INSERT INTO test_users VALUES (1, 'Alice')")
        secure_db.execute("INSERT INTO test_users VALUES (2, 'Bob')")
        secure_db.register_table("users", "test_users")

        # Delete specific record
        secure_db.execute_safe_delete("users", "id = ?", 1)

        # Verify deletion
        result = secure_db.execute("SELECT * FROM test_users")
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0] == (2, "Bob")

    def test_execute_safe_delete_without_where(self, secure_db):
        """Test that DELETE without WHERE is blocked."""
        secure_db.register_table("users", "test_users")

        with pytest.raises(
            ValueError, match="DELETE without WHERE clause is not allowed"
        ):
            secure_db.execute_safe_delete("users", "")

    def test_audit_logging(self, secure_db):
        """Test query audit logging."""
        # Create test table
        secure_db.execute("CREATE TABLE test_users (id INTEGER, name TEXT)")
        secure_db.register_table("users", "test_users")

        # Execute some queries
        secure_db.execute_safe(
            "INSERT INTO {table} VALUES (?, ?)",
            1,
            "Alice",
            table_alias="users",
            query_type=QueryType.INSERT,
        )

        secure_db.execute_safe(
            "SELECT * FROM {table}",
            table_alias="users",
            query_type=QueryType.SELECT,
        )

        # Check audit log
        audit_log = secure_db.get_audit_log()
        assert len(audit_log) == 2
        assert audit_log[0].query_type == QueryType.INSERT
        assert audit_log[1].query_type == QueryType.SELECT

    def test_audit_log_with_errors(self, secure_db):
        """Test that errors are logged in audit."""
        secure_db.register_table("users", "test_users")

        # Try to execute invalid query
        with pytest.raises(ValueError):
            secure_db.execute_safe(
                "SELECT * FROM {table}; DROP TABLE x",
                table_alias="users",
                query_type=QueryType.SELECT,
            )

        # Check audit log
        audit_log = secure_db.get_audit_log()
        assert len(audit_log) == 1
        assert audit_log[0].error is not None
        assert "Query validation failed" in audit_log[0].error

    def test_audit_log_filtering(self, secure_db):
        """Test audit log filtering options."""
        # Create test table
        secure_db.execute("CREATE TABLE test_users (id INTEGER)")
        secure_db.register_table("users", "test_users")

        # Execute various queries
        secure_db.execute_safe(
            "INSERT INTO {table} VALUES (?)",
            1,
            table_alias="users",
            query_type=QueryType.INSERT,
        )

        secure_db.execute_safe(
            "SELECT * FROM {table}",
            table_alias="users",
            query_type=QueryType.SELECT,
        )

        # Try invalid query
        try:
            secure_db.execute_safe(
                "SELECT * FROM {table}; DROP TABLE x",
                table_alias="users",
                query_type=QueryType.SELECT,
            )
        except ValueError:
            pass

        # Filter by query type
        select_logs = secure_db.get_audit_log(query_type=QueryType.SELECT)
        assert len(select_logs) == 2  # One successful, one failed

        # Exclude errors
        success_logs = secure_db.get_audit_log(include_errors=False)
        assert len(success_logs) == 2  # Only successful queries

        # Limit results
        limited_logs = secure_db.get_audit_log(limit=1)
        assert len(limited_logs) == 1

    def test_audit_log_max_entries(self, secure_db):
        """Test that audit log respects max entries limit."""
        secure_db._max_audit_entries = 5
        secure_db.execute("CREATE TABLE test_users (id INTEGER)")
        secure_db.register_table("users", "test_users")

        # Execute more queries than max limit
        for i in range(10):
            secure_db.execute_safe(
                "INSERT INTO {table} VALUES (?)",
                i,
                table_alias="users",
                query_type=QueryType.INSERT,
            )

        # Should only keep last 5 entries
        audit_log = secure_db.get_audit_log()
        assert len(audit_log) == 5

        # Verify they are the most recent
        # The audit entries should have incrementing parameter values from 5-9
        for i, entry in enumerate(audit_log):
            assert entry.params[0] == i + 5

    def test_audit_statistics(self, secure_db):
        """Test audit statistics generation."""
        # Create test table
        secure_db.execute("CREATE TABLE test_users (id INTEGER)")
        secure_db.register_table("users", "test_users")

        # Execute various queries
        secure_db.execute_safe(
            "INSERT INTO {table} VALUES (?)",
            1,
            table_alias="users",
            query_type=QueryType.INSERT,
        )

        secure_db.execute_safe(
            "SELECT * FROM {table}",
            table_alias="users",
            query_type=QueryType.SELECT,
        )

        # Try invalid query
        try:
            secure_db.execute_safe(
                "DROP TABLE {table}",
                table_alias="users",
                query_type=QueryType.DROP,
                validate=False,  # Skip validation to test error handling
            )
        except Exception:
            pass

        stats = secure_db.get_audit_statistics()
        assert stats["total_queries"] >= 2
        # Both queries should succeed, the DROP fails at execution not validation
        assert stats["successful_queries"] >= 2
        assert stats["query_types"]["INSERT"] == 1
        assert stats["query_types"]["SELECT"] == 1

    def test_clear_audit_log(self, secure_db):
        """Test clearing audit log."""
        secure_db.execute("CREATE TABLE test_users (id INTEGER)")
        secure_db.register_table("users", "test_users")

        # Execute some queries
        secure_db.execute_safe(
            "INSERT INTO {table} VALUES (?)",
            1,
            table_alias="users",
            query_type=QueryType.INSERT,
        )

        assert len(secure_db.get_audit_log()) == 1

        # Clear log
        secure_db.clear_audit_log()
        assert len(secure_db.get_audit_log()) == 0

    @pytest.mark.asyncio
    async def test_execute_safe_async(self, secure_db):
        """Test async execution."""
        # Create test table
        secure_db.execute("CREATE TABLE test_users (id INTEGER, name TEXT)")
        secure_db.register_table("users", "test_users")

        # Execute async insert
        await secure_db.execute_safe_async(
            "INSERT INTO {table} VALUES (?, ?)",
            1,
            "Alice",
            table_alias="users",
            query_type=QueryType.INSERT,
        )

        # Execute async select
        result = await secure_db.execute_safe_async(
            "SELECT * FROM {table} WHERE id = ?",
            1,
            table_alias="users",
            query_type=QueryType.SELECT,
        )

        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0] == (1, "Alice")

    def test_default_tables_registration(self):
        """Test that default tables are registered on initialization."""
        infrastructure = Mock()
        secure_db = SecureDatabaseResource(infrastructure)

        # Check default tables are registered
        tables = secure_db.get_registered_tables()
        assert "memory" in tables
        assert "vectors" in tables
        assert "metadata" in tables

    def test_sql_injection_prevention_comprehensive(self, secure_db):
        """Comprehensive test of SQL injection prevention."""
        # Create test table
        secure_db.execute(
            "CREATE TABLE test_users (id INTEGER, name TEXT, admin BOOLEAN)"
        )
        secure_db.execute("INSERT INTO test_users VALUES (1, 'Alice', 0)")
        secure_db.execute("INSERT INTO test_users VALUES (2, 'Admin', 1)")
        secure_db.register_table("users", "test_users")

        # Common SQL injection attempts that should be blocked
        injection_attempts = [
            # Classic injection
            ("SELECT * FROM {table} WHERE id = 1 OR 1=1", "OR 1=1 attack"),
            # String-based injection
            ("SELECT * FROM {table} WHERE name = 'x' OR '1'='1'", "String OR attack"),
            # Comment injection
            ("SELECT * FROM {table} WHERE id = 1--", "Comment injection"),
            # Union injection
            ("SELECT * FROM {table} UNION SELECT * FROM test_users", "UNION attack"),
            # Stacked queries
            ("SELECT * FROM {table}; DELETE FROM test_users", "Stacked queries"),
            # Time-based blind injection
            ("SELECT * FROM {table} WHERE id = SLEEP(5)", "Time-based attack"),
            # Stored procedure execution
            ("EXEC('SELECT * FROM {table}')", "Stored procedure"),
        ]

        for query, attack_type in injection_attempts:
            with pytest.raises(
                ValueError, match="Query validation failed|does not start with expected"
            ):
                secure_db.execute_safe(
                    query,
                    table_alias="users",
                    query_type=QueryType.SELECT,
                )

    def test_parameterized_query_safety(self, secure_db):
        """Test that parameterized queries prevent injection."""
        # Create test table
        secure_db.execute("CREATE TABLE test_users (id INTEGER, name TEXT)")
        secure_db.execute("INSERT INTO test_users VALUES (1, 'Alice')")
        secure_db.execute("INSERT INTO test_users VALUES (2, 'Bob')")
        secure_db.register_table("users", "test_users")

        # Test that normal parameterized queries work
        result = secure_db.execute_safe(
            "SELECT * FROM {table} WHERE id = ?",
            1,  # Normal integer parameter
            table_alias="users",
            query_type=QueryType.SELECT,
        )
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0] == (1, "Alice")

        # Try with string injection in string field
        malicious_name = "'; DROP TABLE test_users; --"
        result = secure_db.execute_safe(
            "SELECT * FROM {table} WHERE name = ?",
            malicious_name,  # Safely parameterized
            table_alias="users",
            query_type=QueryType.SELECT,
        )

        rows = result.fetchall()
        assert len(rows) == 0  # No user with that name

        # Table should still exist
        result = secure_db.execute("SELECT COUNT(*) FROM test_users")
        assert result.fetchone()[0] == 2

        # Test that SQL in parameters doesn't execute
        injection_attempt = "Alice' OR '1'='1"
        result = secure_db.execute_safe(
            "SELECT * FROM {table} WHERE name = ?",
            injection_attempt,  # Treated as literal string
            table_alias="users",
            query_type=QueryType.SELECT,
        )
        rows = result.fetchall()
        assert len(rows) == 0  # No exact match for that string
