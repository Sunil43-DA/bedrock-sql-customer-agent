
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sql_agent import validate_sql_intent


def expect_rejection(question, sql):
    try:
        validate_sql_intent(question, sql)
    except ValueError:
        return

    raise AssertionError(f"Expected rejection for SQL: {sql}")


validate_sql_intent(
    "What is the average customer spend?",
    "SELECT AVG(total_spend) AS average_spend FROM customers",
)

expect_rejection(
    "What is the average customer spend?",
    "SELECT city, AVG(total_spend) FROM customers GROUP BY city",
)

validate_sql_intent(
    "Show total spending for each city",
    "SELECT city, SUM(total_spend) AS total_spending "
    "FROM customers GROUP BY city",
)

validate_sql_intent(
    "Which customer spent the most?",
    "SELECT customer_name, total_spend FROM customers "
    "ORDER BY total_spend DESC LIMIT 1",
)

validate_sql_intent(
    "How many active customers are there?",
    "SELECT COUNT(*) FROM customers "
    "WHERE customer_status = 'Active'",
)

print("PASS: Overall average accepted")
print("PASS: Incorrect grouped average rejected")
print("PASS: City spending accepted")
print("PASS: Highest-spending customer accepted")
print("PASS: Active customer count accepted")
print("\nAll SQL intent tests passed.")
