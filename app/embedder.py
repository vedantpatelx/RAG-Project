import boto3
import json

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

def embed_text(text: str) -> list[float]:
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text})
    )
    return json.loads(response["body"].read())["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    return [embed_text(text) for text in texts]