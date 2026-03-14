#!/usr/bin/env python3
"""
NEVPAZ - Verbindungstest fuer AWS Bedrock EU (Frankfurt).
Testet die Verbindung zu Claude Sonnet 4.6 in eu-central-1.
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def test_verbindung():
    """Testet die Verbindung zu AWS Bedrock EU."""
    print("NEVPAZ Bedrock-Verbindungstest")
    print("=" * 40)

    region = os.getenv("AWS_REGION", "eu-central-1")
    model_id = os.getenv(
        "BEDROCK_MODEL_ID",
        "eu.anthropic.claude-sonnet-4-6-20260214-v1:0"
    )

    print(f"Region:  {region}")
    print(f"Modell:  {model_id}")

    # Pruefe Credentials
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    if not access_key or access_key == "IHRE_AWS_ACCESS_KEY_ID":
        print("\nFEHLER: AWS_ACCESS_KEY_ID nicht konfiguriert.")
        print("Bitte .env.example nach .env kopieren und Credentials eintragen.")
        return False

    print(f"Key:     {access_key[:4]}...{access_key[-4:]}")

    try:
        import boto3

        client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        print("\nSende Test-Anfrage...")

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Antworte nur mit: NEVPAZ Verbindungstest erfolgreich."
                }
            ],
            "temperature": 0,
        })

        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        result = json.loads(response["body"].read())
        antwort = result["content"][0]["text"]

        print(f"Antwort: {antwort}")
        print(f"\nTokens:  {result.get('usage', {})}")
        print("\nVerbindungstest ERFOLGREICH")
        return True

    except Exception as e:
        print(f"\nFEHLER: {e}")
        print("\nMoegliche Ursachen:")
        print("  1. AWS-Credentials falsch oder abgelaufen")
        print("  2. Bedrock nicht in eu-central-1 aktiviert")
        print("  3. Claude Sonnet 4.6 nicht freigeschaltet")
        print("  4. Netzwerkproblem")
        return False


if __name__ == "__main__":
    success = test_verbindung()
    sys.exit(0 if success else 1)
