
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from sql_engine import execute_query


def test_average_spend():
    query = """
        SELECT AVG(total_spend) AS average_spend
        FROM customers
    """

    result = execute_query(query)
    actual = float(result.iloc[0]["average_spend"])

    assert abs(actual - 1290.30) < 0.01, (
        f"Expected 1290.30, got {actual}"
    )

    print("PASS: Average customer spend")


def test_city_spending():
    query = """
        SELECT city, SUM(total_spend) AS total_spending
        FROM customers
        GROUP BY city
    """

    result = execute_query(query)
    actual = dict(zip(result["city"], result["total_spending"]))

    expected = {
        "London": 3000.50,
        "Birmingham": 2200.75,
        "Manchester": 800.00,
        "Leeds": 450.25,
    }

    assert set(actual) == set(expected), (
        f"Unexpected cities: {actual}"
    )

    for city, amount in expected.items():
        assert abs(float(actual[city]) - amount) < 0.01, (
            f"Incorrect total for {city}: {actual[city]}"
        )

    print("PASS: Spending by city")


def test_highest_spending_customer():
    query = """
        SELECT customer_name, total_spend
        FROM customers
        ORDER BY total_spend DESC
        LIMIT 1
    """

    result = execute_query(query)

    assert result.iloc[0]["customer_name"] == "Priya Patel"
    assert abs(float(result.iloc[0]["total_spend"]) - 2200.75) < 0.01

    print("PASS: Highest-spending customer")


if __name__ == "__main__":
    test_average_spend()
    test_city_spending()
    test_highest_spending_customer()

    print("\nAll SQL tests passed.")
