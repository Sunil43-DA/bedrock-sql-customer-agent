
from pathlib import Path
import re
import sqlite3

import pandas as pd


# --------------------------------------------------
# Database configuration
# --------------------------------------------------

DATABASE_FILE = Path(__file__).parent / "customers.db"

ALLOWED_TABLE = "customers"


# --------------------------------------------------
# Validate SQL before execution
# --------------------------------------------------

def validate_query(query: str) -> str:
    """
    Allow one read-only SELECT statement that reads
    only from the customers table.

    This is a learning-project validator. The SQLite
    authorizer below provides an additional enforcement layer.
    """

    if not isinstance(query, str):
        raise ValueError("SQL query must be a string.")

    query = query.strip()

    if not query:
        raise ValueError("SQL query cannot be empty.")

    # Permit one optional trailing semicolon.
    query = query.removesuffix(";").strip()

    # Reject multiple statements and embedded semicolons.
    if ";" in query:
        raise ValueError("Multiple SQL statements are not allowed.")

    # Only SELECT statements are permitted.
    if not re.match(r"(?is)^SELECT\b", query):
        raise ValueError("Only SELECT queries are allowed.")

    # Reject SQL comments.
    if "--" in query or "/*" in query or "*/" in query:
        raise ValueError("SQL comments are not allowed.")

    # Reject common write, schema, and administrative keywords.
    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|"
        r"ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|TRIGGER|"
        r"GRANT|REVOKE|EXEC|EXECUTE)\b",
        re.IGNORECASE,
    )

    if forbidden.search(query):
        raise ValueError("The query contains a forbidden SQL keyword.")

    # Basic table-reference check.
    # SQLite's authorizer below provides the stronger enforcement.
    table_names = re.findall(
        r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)",
        query,
        re.IGNORECASE,
    )

    if not table_names:
        raise ValueError(
            "The query must read from the customers table."
        )

    if any(name.lower() != ALLOWED_TABLE for name in table_names):
        raise ValueError("Only the customers table may be queried.")

    return query


# --------------------------------------------------
# SQLite authorizer
# --------------------------------------------------

def _authorize_sqlite_action(
    action,
    arg1,
    arg2,
    database_name,
    trigger_name,
):
    """
    Allow SELECT operations and reads from customers only.
    Deny all other SQLite actions by default.
    """

    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK

    if action == sqlite3.SQLITE_READ:
        if arg1 and arg1.lower() == ALLOWED_TABLE:
            return sqlite3.SQLITE_OK

        return sqlite3.SQLITE_DENY

    if action == sqlite3.SQLITE_FUNCTION:
        # Permit SQLite functions used by analytical queries,
        # including AVG, SUM, COUNT, ROUND and MAX.
        return sqlite3.SQLITE_OK

    # Deny writes, schema changes, attachment, and other
    # actions not explicitly allowed above.
    return sqlite3.SQLITE_DENY


# --------------------------------------------------
# Execute SQL safely
# --------------------------------------------------

def execute_query(query: str) -> pd.DataFrame:
    """Validate and execute a query against read-only SQLite."""

    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_FILE}. "
            "Run setup_sqlite.py first."
        )

    safe_query = validate_query(query)

    # Open the database in read-only mode.
    database_uri = DATABASE_FILE.resolve().as_uri() + "?mode=ro"

    with sqlite3.connect(
        database_uri,
        uri=True,
        timeout=5,
    ) as connection:

        # SQLite-level safeguards.
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA busy_timeout = 5000")

        # Enforce allowed SQL operations at the database layer.
        connection.set_authorizer(_authorize_sqlite_action)

        # SQLite will reject multiple statements and any operation
        # denied by the authorizer.
        results = pd.read_sql_query(safe_query, connection)

    return results


# --------------------------------------------------
# Standalone test
# --------------------------------------------------

if __name__ == "__main__":
    sql = """
        SELECT
            city,
            ROUND(SUM(total_spend), 2) AS total_spend
        FROM customers
        GROUP BY city
        ORDER BY total_spend DESC
    """

    try:
        results = execute_query(sql)

        print("SQL query results:\n")
        print(results.to_string(index=False))

    except (
        ValueError,
        FileNotFoundError,
        sqlite3.Error,
        pd.errors.DatabaseError,
    ) as error:
        print(f"Query failed: {error}")
