
from pathlib import Path

import boto3
import pandas as pd


# --------------------------------------------------
# Configuration
# --------------------------------------------------

DATA_FILE = Path(__file__).parent / "customers.csv"

AWS_REGION = "eu-north-1"
BEDROCK_MODEL_ID = "eu.amazon.nova-lite-v1:0"


# --------------------------------------------------
# Load customer data
# --------------------------------------------------

def load_customers() -> pd.DataFrame:
    """Load and validate customer records from CSV."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Customer data file not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    required_columns = {
        "customer_id",
        "customer_name",
        "city",
        "total_spend",
        "customer_status",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    if df.empty:
        return df

    df["total_spend"] = pd.to_numeric(
        df["total_spend"], errors="raise"
    )

    return df


# --------------------------------------------------
# Create the Amazon Bedrock client
# --------------------------------------------------

def create_bedrock_client():
    """Create a client for Amazon Bedrock Runtime."""

    return boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
    )


# --------------------------------------------------
# Answer questions using Python and Pandas
# --------------------------------------------------

def answer_question(
    question: str,
    df: pd.DataFrame,
) -> str | None:
    """Calculate answers from actual customer records."""

    question = question.lower().strip()

    if df.empty:
        return "There are no customer records to analyse."

    # Highest-spending customer
    if "most" in question and (
        "spent" in question or "spend" in question
    ):
        customer = df.loc[df["total_spend"].idxmax()]

        return (
            f'{customer["customer_name"]} spent the most: '
            f'£{customer["total_spend"]:.2f}.'
        )

    # Average customer spend
    if "average" in question and (
        "spend" in question or "spent" in question
    ):
        average_spend = df["total_spend"].mean()

        return (
            f"The average customer spend is "
            f"£{average_spend:.2f}."
        )

    # Total spending by city
    if "spend by city" in question:
        totals = (
            df.groupby("city")["total_spend"]
            .sum()
            .sort_values(ascending=False)
        )

        return totals.to_string(
            header=["Total Spend (£)"],
            float_format=lambda value: f"£{value:,.2f}",
        )

    # Count active customers
    if "how many" in question and "active" in question:
        count = (
            df["customer_status"]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("active")
            .sum()
        )

        return f"There are {count} active customers."

    # Display all customers
    if (
        "all customers" in question
        or "show customers" in question
    ):
        return df.to_string(index=False)

    # Return None when the local rules cannot answer.
    return None


# --------------------------------------------------
# Prepare a safe summary for Bedrock
# --------------------------------------------------

def build_customer_summary(df: pd.DataFrame) -> dict:
    """Create aggregate statistics from customer data."""

    if df.empty:
        return {
            "customer_count": 0,
            "total_spend": 0,
            "average_spend": 0,
            "active_customers": 0,
            "city_spend": {},
        }

    active_count = (
        df["customer_status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("active")
        .sum()
    )

    city_totals = (
        df.groupby("city")["total_spend"]
        .sum()
        .to_dict()
    )

    return {
        "customer_count": len(df),
        "total_spend": round(
            float(df["total_spend"].sum()), 2
        ),
        "average_spend": round(
            float(df["total_spend"].mean()), 2
        ),
        "active_customers": int(active_count),
        "city_spend": {
            str(city): round(float(total), 2)
            for city, total in city_totals.items()
        },
    }


# --------------------------------------------------
# Answer general questions using Amazon Bedrock
# --------------------------------------------------

def ask_bedrock(
    question: str,
    df: pd.DataFrame,
    bedrock_client,
) -> str:
    """Use Nova Lite to explain the available data summary."""

    summary = build_customer_summary(df)

    response = bedrock_client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            "You are a customer data assistant. "
                            "Answer the user's question using only "
                            "the supplied customer data summary. "
                            "Do not invent names, figures, or facts. "
                            "If the summary lacks the information "
                            "needed, explain that limitation. "
                            "Format monetary values in GBP (£).\n\n"
                            f"Customer data summary: {summary}\n\n"
                            f"Question: {question}"
                        )
                    }
                ],
            }
        ],
        inferenceConfig={
            "maxTokens": 300,
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
        return "Bedrock returned no text response."

    return "\n".join(text_parts)


# --------------------------------------------------
# Interactive agent
# --------------------------------------------------

def main():
    """Run the customer data agent."""

    try:
        customers = load_customers()
    except (
        FileNotFoundError,
        ValueError,
        pd.errors.ParserError,
    ) as error:
        print(f"Error loading customer data: {error}")
        return

    try:
        bedrock_client = create_bedrock_client()
    except Exception as error:
        print(f"Could not initialise the Bedrock client: {error}")
        return

    print("=" * 45)
    print("Customer Data Agent")
    print("=" * 45)
    print(f"Loaded {len(customers)} customer records.")
    print(f"AWS region: {AWS_REGION}")
    print("Python calculations and Bedrock are available.")
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

        # Try exact local calculations first.
        answer = answer_question(question, customers)

        # Use Bedrock if a local rule does not match.
        if answer is None:
            try:
                answer = ask_bedrock(
                    question,
                    customers,
                    bedrock_client,
                )
            except Exception as error:
                print(f"Bedrock request failed: {error}\n")
                continue

        print(f"Agent: {answer}\n")


if __name__ == "__main__":
    main()
