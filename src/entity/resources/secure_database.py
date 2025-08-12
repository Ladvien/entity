"""Secure database resource with SQL injection prevention."""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from entity.infrastructure.protocols import DatabaseInfrastructure
from entity.resources.database import DatabaseResource


class QueryType(Enum):
    """Types of SQL queries for validation."""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"
    TRUNCATE = "TRUNCATE"


@dataclass
class QueryAuditEntry:
    """Audit entry for executed queries."""

    timestamp: datetime
    query: str
    params: Tuple[Any, ...]
    table_name: Optional[str]
    query_type: QueryType
    sanitized: bool
    validation_passed: bool
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None


class SQLQueryValidator:
    """Validator for SQL queries to prevent injection attacks."""

    SUSPICIOUS_PATTERNS = [
        r";\s*(DROP|DELETE|TRUNCATE|ALTER|CREATE|INSERT|UPDATE)",
        r"--\s*",
        r"/\*.*\*/",
        r"\bUNION\b.*\bSELECT\b",
        r"\bOR\b\s+\d+\s*=\s*\d+",
        r"\bOR\b\s*'[^']*'\s*=\s*'[^']*'",
        r"(SLEEP|BENCHMARK|WAITFOR|DELAY)\s*\(",
        r"(EXEC|EXECUTE)\s*\(",
        r"xp_cmdshell",
        r"(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)",
    ]

    VALID_TABLE_NAME_PATTERN = re.compile(
        r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$"
    )

    VALID_COLUMN_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    def __init__(self, strict_mode: bool = True):
        """Initialize the validator.

        Args:
            strict_mode: If True, applies stricter validation rules
        """
        self.strict_mode = strict_mode
        self.logger = logging.getLogger(__name__)
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.SUSPICIOUS_PATTERNS
        ]

    def validate_query(
        self, query: str, query_type: Optional[QueryType] = None
    ) -> Tuple[bool, List[str]]:
        """Validate a SQL query for injection attempts.

        Args:
            query: The SQL query to validate
            query_type: Expected query type

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        for pattern in self._compiled_patterns:
            if pattern.search(query):
                issues.append(f"Suspicious pattern detected: {pattern.pattern}")

        if self.strict_mode and query_type:
            if not query.strip().upper().startswith(query_type.value):
                issues.append(f"Query does not start with expected {query_type.value}")

        if query.count(";") > 1:
            issues.append(
                "Multiple semicolons detected - possible multi-statement attack"
            )

        return len(issues) == 0, issues

    def validate_table_name(self, table_name: str) -> bool:
        """Validate a table name against injection patterns.

        Args:
            table_name: The table name to validate

        Returns:
            True if valid, False otherwise
        """
        if not table_name:
            return False

        if not self.VALID_TABLE_NAME_PATTERN.match(table_name):
            self.logger.warning(f"Invalid table name format: {table_name}")
            return False

        suspicious_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "EXEC", "UNION"]
        table_upper = table_name.upper()
        for keyword in suspicious_keywords:
            if keyword in table_upper:
                self.logger.warning(f"Suspicious keyword in table name: {table_name}")
                return False

        return True

    def validate_column_names(self, columns: List[str]) -> Tuple[bool, List[str]]:
        """Validate column names for injection attempts.

        Args:
            columns: List of column names to validate

        Returns:
            Tuple of (all_valid, list_of_invalid_columns)
        """
        invalid_columns = []

        for column in columns:
            if not self.VALID_COLUMN_NAME_PATTERN.match(column):
                invalid_columns.append(column)

        return len(invalid_columns) == 0, invalid_columns

    def sanitize_identifier(self, identifier: str) -> str:
        """Sanitize a database identifier (table/column name).

        Args:
            identifier: The identifier to sanitize

        Returns:
            Sanitized identifier
        """
        sanitized = re.sub(r"[^a-zA-Z0-9_.]", "", identifier)

        if sanitized and not re.match(r"^[a-zA-Z_]", sanitized):
            sanitized = "_" + sanitized

        return sanitized


class SecureDatabaseResource(DatabaseResource):
    """Secure database resource with SQL injection prevention."""

    def __init__(
        self,
        infrastructure: DatabaseInfrastructure,
        enable_query_logging: bool = True,
        max_audit_entries: int = 10000,
        strict_validation: bool = True,
    ):
        """Initialize the secure database resource.

        Args:
            infrastructure: The database infrastructure
            enable_query_logging: Whether to log queries for audit
            max_audit_entries: Maximum number of audit entries to keep
            strict_validation: Whether to use strict validation mode
        """
        super().__init__(infrastructure)

        self._table_registry: Dict[str, str] = {}
        self._query_validator = SQLQueryValidator(strict_mode=strict_validation)
        self._audit_log: List[QueryAuditEntry] = []
        self._enable_query_logging = enable_query_logging
        self._max_audit_entries = max_audit_entries
        self._allowed_query_types: Set[QueryType] = set(QueryType)
        self.logger = logging.getLogger(__name__)

        self._register_default_tables()

    def _register_default_tables(self):
        """Register default safe tables."""
        default_tables = {
            "memory": "memory",
            "vectors": "vectors",
            "metadata": "metadata",
            "logs": "logs",
            "metrics": "metrics",
        }

        for alias, table_name in default_tables.items():
            try:
                self.register_table(alias, table_name)
            except ValueError:
                pass

    def register_table(self, alias: str, table_name: str) -> None:
        """Register a table with validated name.

        Args:
            alias: Alias for the table
            table_name: Actual table name in the database

        Raises:
            ValueError: If table name is invalid
        """
        if not self._query_validator.validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        if not alias or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", alias):
            raise ValueError(f"Invalid table alias: {alias}")

        self._table_registry[alias] = table_name
        self.logger.info(f"Registered table: {alias} -> {table_name}")

    def unregister_table(self, alias: str) -> None:
        """Unregister a table alias.

        Args:
            alias: The alias to unregister
        """
        if alias in self._table_registry:
            del self._table_registry[alias]
            self.logger.info(f"Unregistered table: {alias}")

    def get_registered_tables(self) -> Dict[str, str]:
        """Get all registered table mappings.

        Returns:
            Dictionary of alias to table name mappings
        """
        return self._table_registry.copy()

    def set_allowed_query_types(self, query_types: List[QueryType]) -> None:
        """Set allowed query types for execution.

        Args:
            query_types: List of allowed query types
        """
        self._allowed_query_types = set(query_types)
        self.logger.info(
            f"Allowed query types set to: {[qt.value for qt in query_types]}"
        )

    def execute_safe(
        self,
        query_template: str,
        *params: Any,
        table_alias: Optional[str] = None,
        query_type: Optional[QueryType] = None,
        validate: bool = True,
    ) -> Any:
        """Execute a query with SQL injection prevention.

        Args:
            query_template: Query template with {table} placeholder
            params: Query parameters for safe substitution
            table_alias: Alias of the registered table
            query_type: Expected query type
            validate: Whether to validate the query

        Returns:
            Query execution result

        Raises:
            ValueError: If validation fails or table not registered
            RuntimeError: If query execution fails
        """
        start_time = datetime.now()
        audit_entry = QueryAuditEntry(
            timestamp=start_time,
            query=query_template,
            params=params,
            table_name=None,
            query_type=query_type or QueryType.SELECT,
            sanitized=False,
            validation_passed=False,
        )

        try:
            if query_type and query_type not in self._allowed_query_types:
                raise ValueError(f"Query type {query_type.value} is not allowed")

            if table_alias:
                table_name = self._table_registry.get(table_alias)
                if not table_name:
                    raise ValueError(f"Unregistered table alias: {table_alias}")
                query = query_template.format(table=table_name)
                audit_entry.table_name = table_name
            else:
                query = query_template

            if validate:
                is_valid, issues = self._query_validator.validate_query(
                    query, query_type
                )
                if not is_valid:
                    raise ValueError(f"Query validation failed: {'; '.join(issues)}")
                audit_entry.validation_passed = True

            result = self.execute(query, *params)

            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            audit_entry.execution_time_ms = execution_time

            return result

        except Exception as e:
            audit_entry.error = str(e)
            self.logger.error(f"Query execution failed: {e}")
            raise

        finally:
            if self._enable_query_logging:
                self._add_audit_entry(audit_entry)

    def execute_safe_select(
        self, table_alias: str, columns: List[str], where_clause: str = "", *params: Any
    ) -> Any:
        """Execute a safe SELECT query.

        Args:
            table_alias: Alias of the registered table
            columns: List of column names to select
            where_clause: Optional WHERE clause (without 'WHERE' keyword)
            params: Parameters for the WHERE clause

        Returns:
            Query result
        """
        is_valid, invalid_cols = self._query_validator.validate_column_names(columns)
        if not is_valid:
            raise ValueError(f"Invalid column names: {invalid_cols}")

        columns_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {columns_str} FROM {{table}}"

        if where_clause:
            query += f" WHERE {where_clause}"

        return self.execute_safe(
            query, *params, table_alias=table_alias, query_type=QueryType.SELECT
        )

    def execute_safe_insert(self, table_alias: str, data: Dict[str, Any]) -> Any:
        """Execute a safe INSERT query.

        Args:
            table_alias: Alias of the registered table
            data: Dictionary of column names to values

        Returns:
            Query result
        """
        if not data:
            raise ValueError("No data to insert")

        columns = list(data.keys())
        is_valid, invalid_cols = self._query_validator.validate_column_names(columns)
        if not is_valid:
            raise ValueError(f"Invalid column names: {invalid_cols}")

        columns_str = ", ".join(columns)
        placeholders = ", ".join(["?" for _ in columns])
        values = tuple(data.values())

        query = f"INSERT INTO {{table}} ({columns_str}) VALUES ({placeholders})"

        return self.execute_safe(
            query, *values, table_alias=table_alias, query_type=QueryType.INSERT
        )

    def execute_safe_update(
        self,
        table_alias: str,
        updates: Dict[str, Any],
        where_clause: str,
        *where_params: Any,
    ) -> Any:
        """Execute a safe UPDATE query.

        Args:
            table_alias: Alias of the registered table
            updates: Dictionary of column names to new values
            where_clause: WHERE clause (without 'WHERE' keyword)
            where_params: Parameters for the WHERE clause

        Returns:
            Query result
        """
        if not updates:
            raise ValueError("No updates specified")

        columns = list(updates.keys())
        is_valid, invalid_cols = self._query_validator.validate_column_names(columns)
        if not is_valid:
            raise ValueError(f"Invalid column names: {invalid_cols}")

        set_clauses = [f"{col} = ?" for col in columns]
        set_str = ", ".join(set_clauses)

        query = f"UPDATE {{table}} SET {set_str}"
        if where_clause:
            query += f" WHERE {where_clause}"

        all_params = list(updates.values()) + list(where_params)

        return self.execute_safe(
            query, *all_params, table_alias=table_alias, query_type=QueryType.UPDATE
        )

    def execute_safe_delete(
        self, table_alias: str, where_clause: str, *params: Any
    ) -> Any:
        """Execute a safe DELETE query.

        Args:
            table_alias: Alias of the registered table
            where_clause: WHERE clause (without 'WHERE' keyword)
            params: Parameters for the WHERE clause

        Returns:
            Query result
        """
        if not where_clause:
            raise ValueError("DELETE without WHERE clause is not allowed for safety")

        query = f"DELETE FROM {{table}} WHERE {where_clause}"

        return self.execute_safe(
            query, *params, table_alias=table_alias, query_type=QueryType.DELETE
        )

    def _add_audit_entry(self, entry: QueryAuditEntry) -> None:
        """Add an entry to the audit log.

        Args:
            entry: The audit entry to add
        """
        self._audit_log.append(entry)

        if len(self._audit_log) > self._max_audit_entries:
            self._audit_log = self._audit_log[-self._max_audit_entries :]

    def get_audit_log(
        self,
        limit: Optional[int] = None,
        query_type: Optional[QueryType] = None,
        include_errors: bool = True,
    ) -> List[QueryAuditEntry]:
        """Get audit log entries.

        Args:
            limit: Maximum number of entries to return
            query_type: Filter by query type
            include_errors: Whether to include failed queries

        Returns:
            List of audit entries
        """
        entries = self._audit_log

        if query_type:
            entries = [e for e in entries if e.query_type == query_type]

        if not include_errors:
            entries = [e for e in entries if e.error is None]

        if limit:
            entries = entries[-limit:]

        return entries

    def clear_audit_log(self) -> None:
        """Clear the audit log."""
        self._audit_log.clear()
        self.logger.info("Audit log cleared")

    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get statistics from the audit log.

        Returns:
            Dictionary of audit statistics
        """
        if not self._audit_log:
            return {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "avg_execution_time_ms": 0,
                "query_types": {},
            }

        total = len(self._audit_log)
        successful = sum(1 for e in self._audit_log if e.error is None)
        failed = total - successful

        exec_times = [
            e.execution_time_ms for e in self._audit_log if e.execution_time_ms
        ]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0

        query_types = {}
        for entry in self._audit_log:
            qt = entry.query_type.value
            query_types[qt] = query_types.get(qt, 0) + 1

        return {
            "total_queries": total,
            "successful_queries": successful,
            "failed_queries": failed,
            "avg_execution_time_ms": avg_exec_time,
            "query_types": query_types,
        }

    async def execute_safe_async(
        self,
        query_template: str,
        *params: Any,
        table_alias: Optional[str] = None,
        query_type: Optional[QueryType] = None,
        validate: bool = True,
    ) -> Any:
        """Async version of execute_safe.

        Args:
            query_template: Query template with {table} placeholder
            params: Query parameters for safe substitution
            table_alias: Alias of the registered table
            query_type: Expected query type
            validate: Whether to validate the query

        Returns:
            Query execution result
        """
        return await asyncio.to_thread(
            self.execute_safe,
            query_template,
            *params,
            table_alias=table_alias,
            query_type=query_type,
            validate=validate,
        )
