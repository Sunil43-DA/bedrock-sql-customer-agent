
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sql_engine import validate_query, execute_query


def expect_rejection(label, query):
    try:
        validate_query(query)
    except (ValueError, RuntimeError):
        print(f"PASS: {label} rejected")
        return

    raise AssertionError(
        f"FAIL: {label} was accepted: {query}"
    )


def expect_execution_rejection(label, query):
    try:
        execute_query(query)
    except Exception:
        print(f"PASS: {label} blocked during execution")
        return

    raise AssertionError(
        f"FAIL: {label} unexpectedly executed: {query}"
    )


def main():
    # 1. A valid SELECT query should be accepted.
    validate_query(
        "SELECT customer_name FROM customers"
    )
    print("PASS: Valid SELECT accepted")

    # 2. Reject destructive statements.
    expect_rejection(
        "DELETE statement",
        "DELETE FROM customers",
    )

    expect_rejection(
        "DROP statement",
        "DROP TABLE customers",
    )

    expect_rejection(
        "UPDATE statement",
        "UPDATE customers SET total_spend = 0",
    )

    # 3. Reject unknown tables.
    expect_rejection(
        "Unknown table",
        "SELECT * FROM employees",
    )

    # 4. Reject multiple SQL statements.
    expect_rejection(
        "Multiple SQL statements",
        "SELECT * FROM customers; DROP TABLE customers",
    )

    # 5. Reject unknown tables in JOINs.
    expect_rejection(
        "JOIN to unknown table",
        "SELECT c.customer_name "
        "FROM customers c JOIN employees e "
        "ON c.customer_id = e.customer_id",
    )

    # 6. Reject direct access to SQLite system tables.
    expect_rejection(
        "SQLite system table",
        "SELECT name FROM sqlite_master",
    )

    # 7. Reject SQL comments.
    expect_rejection(
        "Line comment",
        "SELECT customer_name FROM customers -- comment",
    )

    expect_rejection(
        "Block comment",
        "SELECT customer_name FROM customers /* comment */",
    )

    # 8. Reject a write operation hidden in a WITH clause.
    expect_rejection(
        "WITH clause containing DELETE",
        "WITH removed AS (DELETE FROM customers RETURNING *) "
        "SELECT * FROM removed",
    )

    # 9. Valid aggregate queries should remain accepted.
    validate_query(
        "SELECT AVG(total_spend) FROM customers"
    )
    print("PASS: AVG query accepted")

    validate_query(
        "SELECT city, SUM(total_spend) "
        "FROM customers GROUP BY city"
    )
    print("PASS: SUM query accepted")

    validate_query(
        "SELECT COUNT(*) FROM customers"
    )
    print("PASS: COUNT query accepted")

    # 10. Execute a valid read-only query.
    result = execute_query(
        "SELECT COUNT(*) AS customer_count FROM customers"
    )

    count = int(result.iloc[0]["customer_count"])
    assert count == 5, f"Expected 5 customers, got {count}"

    print("PASS: Read-only query execution")
    print("PASS: Customer count is 5")

    # 11. Verify the database authorizer blocks system-table reads.
    expect_execution_rejection(
        "System table access",
        "SELECT name FROM sqlite_master",
    )

    print("\nAll SQL security tests passed.")


if __name__ == "__main__":
    main()
