import json
import boto3
from pinecone import Pinecone

secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
secret = secrets_client.get_secret_value(SecretId='rag-project/env')
secrets = json.loads(secret['SecretString'])

pc = Pinecone(api_key=secrets['PINECONE_API_KEY'])
index = pc.Index(secrets['PINECONE_INDEX_NAME'])

# List all vectors and filter by filename
results = index.query(
    vector=[0.0] * 1024,
    top_k=100,
    include_metadata=True
)

ids_to_delete = []
for match in results['matches']:
    filename = match['metadata'].get('filename', '')
    if 'test-trigger' in filename:
        ids_to_delete.append(match['id'])
        print(f"Found: {filename} -> {match['id']}")

print(f"\nTotal to delete: {len(ids_to_delete)}")

if ids_to_delete:
    index.delete(ids=ids_to_delete)
    print("Deleted!")
else:
    print("Nothing to delete.")