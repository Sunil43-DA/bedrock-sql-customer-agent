
import boto3

REGION = "eu-north-1"
MODEL_ID = "eu.amazon.nova-lite-v1:0"

client = boto3.client("bedrock-runtime", region_name=REGION)

try:
    response = client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": "Reply with exactly: Bedrock connection successful."}
                ],
            }
        ],
        inferenceConfig={
            "maxTokens": 30,
            "temperature": 0,
        },
    )

    answer = response["output"]["message"]["content"][0]["text"]
    print("Bedrock response:", answer)

except Exception as exc:
    print(f"Bedrock request failed: {exc}")
