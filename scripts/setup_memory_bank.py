#!/usr/bin/env python3
"""
Create (or list) a Vertex AI Reasoning Engine with Memory Bank.
Works without gcloud if you are authenticated via one of:
  - Cloud Shell (automatic)
  - GOOGLE_APPLICATION_CREDENTIALS pointing to a service account JSON
  - gcloud auth application-default login

Usage:
  pip install google-cloud-aiplatform
  python scripts/setup_memory_bank.py --project fastapi-test-493805
  python scripts/setup_memory_bank.py --project fastapi-test-493805 --list-only
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision Memory Bank (Reasoning Engine)")
    parser.add_argument("--project", default="fastapi-test-493805")
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--display-name", default="whatsapp-repair-memory-bank")
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args()

    try:
        import vertexai
        from vertexai import types
    except ImportError:
        print("Install: pip install 'google-cloud-aiplatform>=1.111.0'", file=sys.stderr)
        return 1

    client = vertexai.Client(project=args.project, location=args.region)
    parent = f"projects/{args.project}/locations/{args.region}"

    print(f"Project: {args.project}")
    print(f"Region:  {args.region}\n")

    # List existing engines (best-effort; API surface may vary by SDK version)
    try:
        listed = client.agent_engines.list()
        engines = list(listed) if listed is not None else []
        if engines:
            print("Existing Reasoning Engines:")
            for eng in engines:
                name = getattr(getattr(eng, "api_resource", eng), "name", str(eng))
                print(f"  - {name}")
        else:
            print("No Reasoning Engines found (or list returned empty).")
    except Exception as e:
        print(f"(Could not list engines: {e})")

    if args.list_only:
        print("\nIf you see a name above, set VERTEX_AGENT_ENGINE_NAME to that value on Cloud Run.")
        return 0

    embed = (
        f"projects/{args.project}/locations/{args.region}"
        "/publishers/google/models/text-embedding-005"
    )
    gen_model = (
        f"projects/{args.project}/locations/{args.region}"
        "/publishers/google/models/gemini-2.5-flash"
    )
    memory_config = types.ReasoningEngineContextSpecMemoryBankConfig(
        similarity_search_config=types.ReasoningEngineContextSpecMemoryBankConfigSimilaritySearchConfig(
            embedding_model=embed
        ),
        generation_config=types.ReasoningEngineContextSpecMemoryBankConfigGenerationConfig(
            model=gen_model
        ),
    )

    print(f"\nCreating Reasoning Engine '{args.display_name}' (1–3 min)...")
    agent_engine = client.agent_engines.create(
        config={"context_spec": {"memory_bank_config": memory_config}}
    )
    name = agent_engine.api_resource.name
    print("\n" + "=" * 60)
    print("SUCCESS. Add to Cloud Run environment:")
    print(f"  VERTEX_AGENT_ENGINE_NAME={name}")
    print(f"  GOOGLE_CLOUD_REGION={args.region}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
