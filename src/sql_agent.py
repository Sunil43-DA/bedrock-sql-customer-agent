
import re
import sys
from pathlib import Path

import boto3

# Allow imports from the same src directory.
sys.path.insert(0, str(Path(__file__).parent))

from sql_engine import execute_query


# --------------------------------------------------
# Configuration
# --------------------------------------------------

AWS_REGION = "eu-north-1"
MODEL_ID = "eu.amazon.nova-lite-v1:0"

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
)


# --------------------------------------------------
# Generate SQL using Amazon Bedrock
# --------------------------------------------------

def generate_sql(question: str) -> str:
    """Ask Bedrock to generate a read-only SQLite query."""

    prompt = """
You generate SQLite SELECT queries for a customer database.

Available table:
customers(
    customer_id,
    customer_name,
    city,
    total_spend,
    customer_status
)

Rules:
- Return exactly one SQL SELECT query.
- Query only the customers table.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
- Do not use SQL comments.
- Do not include Markdown code fences.
- Do not invent table or column names.
- Use SQLite-compatible SQL.
- For average spending across all customers, use AVG(total_spend)
  without GROUP BY or LIMIT.
- For total spending by city, use SUM(total_spend) and GROUP BY city.
- For the highest-spending customer, order by total_spend DESC
  and use LIMIT 1.
- For the number of active customers, count rows where
  customer_status = 'Active'.
- Return only the SQL query.
"""

    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            f"{prompt}\n"
                            f"User question: {question}\n"
                            "Return the SQL query only."
                        )
                    }
                ],
            }
        ],
        inferenceConfig={
            "maxTokens": 250,
            "temperature": 0,
        },
    )

    content = response["output"]["message"]["content"]

    text_parts = [
        item["text"]
        for item in content
        if "text" in item
    ]

    if not text_parts:
        raise ValueError("Bedrock returned no SQL query.")

    sql = "\n".join(text_parts).strip()

    # Remove optional Markdown fences.
    sql = re.sub(
        r"^```(?:sql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE,
    )
    sql = re.sub(r"\s*```$", "", sql)

    sql = sql.strip()

    if not sql:
        raise ValueError("Bedrock returned an empty SQL query.")

    return sql


# --------------------------------------------------
# Validate SQL intent
# --------------------------------------------------

def validate_sql_intent(question: str, sql: str) -> None:
    """
    Reject common mismatches between the question and generated SQL.

    This is a learning-stage semantic safeguard, not a complete
    SQL security validator. execute_query() must still validate SQL.
    """

    question_lower = question.lower()
    sql_lower = sql.lower()

    # Remove whitespace for reliable function matching.
    compact_sql = re.sub(r"\s+", "", sql_lower)

    # Overall average customer spending.
    average_patterns = (
        "average customer spend",
        "average spend",
        "average spending",
        "mean customer spend",
    )

    if any(term in question_lower for term in average_patterns):
        if not re.search(r"\bavg\s*\(\s*total_spend\s*\)", sql_lower):
            raise ValueError(
                "Intent validation failed: the query must calculate "
                "AVG(total_spend)."
            )

        if re.search(r"\bgroup\s+by\b", sql_lower):
            raise ValueError(
                "Intent validation failed: an overall average should "
                "not be grouped by city."
            )

        if re.search(r"\blimit\b", sql_lower):
            raise ValueError(
                "Intent validation failed: an overall average should "
                "not be restricted with LIMIT."
            )

    # Total spending by city.
    city_spending_patterns = (
        "spending by city",
        "spend by city",
        "total spend by city",
        "total spending for each city",
        "spending for each city",
    )

    if any(term in question_lower for term in city_spending_patterns):
        if not re.search(r"\bgroup\s+by\s+city\b", sql_lower):
            raise ValueError(
                "Intent validation failed: city spending requires "
                "GROUP BY city."
            )

        if not re.search(r"\bsum\s*\(\s*total_spend\s*\)", sql_lower):
            raise ValueError(
                "Intent validation failed: city spending requires "
                "SUM(total_spend)."
            )

    # Highest-spending customer.
    highest_spender_patterns = (
        "highest-spending customer",
        "highest spending customer",
        "customer spent the most",
        "who spent the most",
        "biggest spender",
    )

    if any(term in question_lower for term in highest_spender_patterns):
        if not re.search(
            r"\border\s+by\s+(?:customers\.)?total_spend\s+desc\b",
            sql_lower,
        ):
            raise ValueError(
                "Intent validation failed: the query must order "
                "total_spend from highest to lowest."
            )

        if not re.search(r"\blimit\s+1\b", sql_lower):
            raise ValueError(
                "Intent validation failed: the query must return "
                "only the highest-spending customer."
            )

    # Count active customers.
    active_count_patterns = (
        "number of active customers",
        "count of active customers",
        "how many active customers",
        "active customer count",
    )

    if any(term in question_lower for term in active_count_patterns):
        if not re.search(r"\bcount\s*\(", sql_lower):
            raise ValueError(
                "Intent validation failed: the query must count customers."
            )

        if not re.search(
            r"""customer_status\s*=\s*['"]active['"]""",
            sql_lower,
        ):
            raise ValueError(
                "Intent validation failed: the query must filter "
                "for Active customers."
            )


# --------------------------------------------------
# Execute SQL through the existing SQL engine
# --------------------------------------------------

def run_sql_agent(question: str) -> str:
    """Generate SQL, check intent, execute, and format results."""

    sql = generate_sql(question)

    print(f"\nGenerated SQL:\n{sql}\n")

    # Check whether the generated query matches common question intents.
    validate_sql_intent(question, sql)

    # The existing SQL engine must validate the query and use
    # a read-only database connection before execution.
    results = execute_query(sql)

    if results.empty:
        return "The query returned no results."

    return results.to_string(index=False)


# --------------------------------------------------
# Interactive application
# --------------------------------------------------

def main():
    print("=" * 45)
    print("Bedrock SQL Customer Agent")
    print("=" * 45)
    print("Database: local SQLite")
    print(f"AWS region: {AWS_REGION}")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()

        except (EOFError, KeyboardInterrupt):
            print("\nAgent: Goodbye!")
            break

        if question.lower() == "exit":
            print("Agent: Goodbye!")
            break

        if not question:
            print("Agent: Please enter a question.\n")
            continue

        try:
            answer = run_sql_agent(question)
            print(f"Agent:\n{answer}\n")

        except Exception as error:
            print(f"Agent error: {error}\n")


if __name__ == "__main__":
    main()
