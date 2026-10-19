
from pathlib import Path
import sqlite3

import pandas as pd


# Locate the existing customer CSV.
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "customers.csv"
DATABASE_FILE = BASE_DIR / "customers.db"


def setup_database():
    """Load CSV customer data into a local SQLite database."""

    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Customer CSV not found: {CSV_FILE}"
        )

    customers = pd.read_csv(CSV_FILE)

    required_columns = {
        "customer_id",
        "customer_name",
        "city",
        "total_spend",
        "customer_status",
    }

    missing = required_columns - set(customers.columns)

    if missing:
        raise ValueError(
            f"Missing CSV columns: {sorted(missing)}"
        )

    customers["total_spend"] = pd.to_numeric(
        customers["total_spend"], errors="raise"
    )

    with sqlite3.connect(DATABASE_FILE) as connection:
        customers.to_sql(
            "customers",
            connection,
            if_exists="replace",
            index=False,
        )

        # Verify the number of records loaded.
        count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

    print("SQLite database created successfully.")
    print(f"Database: {DATABASE_FILE}")
    print(f"Customer records loaded: {count}")


if __name__ == "__main__":
    setup_database()
