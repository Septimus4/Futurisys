#!/usr/bin/env python3
"""
Script to update the OpenAPI specification file from the running API.
"""

import json
import sys
import urllib.request
from pathlib import Path


def update_openapi_spec(api_url: str = "http://localhost:8000", output_file: str = "openapi.json") -> None:
    """Update the OpenAPI specification file."""
    try:
        # Get the OpenAPI spec from the running API
        with urllib.request.urlopen(  # noqa: S310
            f"{api_url}/openapi.json"
        ) as response:
            openapi_data = json.loads(response.read().decode())

        # Write formatted JSON to file
        output_path = Path(__file__).parent.parent / output_file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(openapi_data, f, indent=2, ensure_ascii=False)

        print(f"OpenAPI specification updated: {output_path}")
        print(f"Title: {openapi_data.get('info', {}).get('title', 'Unknown')}")
        print(f"Version: {openapi_data.get('info', {}).get('version', 'Unknown')}")
        print(f"Endpoints: {len(openapi_data.get('paths', {}))}")

    except Exception as e:
        print(f"Failed to update OpenAPI spec: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update OpenAPI specification")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", default="openapi.json", help="Output file path")

    args = parser.parse_args()
    update_openapi_spec(args.api_url, args.output)
