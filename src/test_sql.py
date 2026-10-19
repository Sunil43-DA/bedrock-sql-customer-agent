
from pathlib import Path
import sqlite3


DATABASE_FILE = Path(__file__).parent / "customers.db"


def main():
    with sqlite3.connect(DATABASE_FILE) as connection:
        query = """
            SELECT
                city,
                ROUND(SUM(total_spend), 2) AS total_spend
            FROM customers
            GROUP BY city
            ORDER BY total_spend DESC;
        """

        results = connection.execute(query).fetchall()

    print("Total customer spend by city:\n")

    for city, total in results:
        print(f"{city}: £{total:,.2f}")


if __name__ == "__main__":
    main()
