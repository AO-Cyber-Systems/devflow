#!/usr/bin/env python3
"""Generate JSON response snapshots for all RPC methods.

These snapshots are used by Swift contract tests to verify
that Swift models can decode actual Python responses.
"""

import json
import subprocess
import sys
from pathlib import Path

SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"

# RPC methods to snapshot with their test parameters
RPC_METHODS = [
    # System
    ("system.ping", {}),
    ("system.version", {}),
    ("system.info", {}),
    ("system.doctor", {}),
    ("system.full_doctor", {}),
    ("system.package_doctor", {}),
    ("system.check_packages", {}),

    # Projects
    ("projects.list", {}),

    # Config
    ("config.get_global", {}),

    # Infrastructure
    ("infra.status", {}),

    # Domains
    ("domains.list", {}),

    # Docs
    ("docs.list_docs", {}),
    ("docs.get_doc_types", {}),
    ("docs.get_doc_formats", {}),

    # Code
    ("code.get_supported_languages", {}),
    ("code.get_entity_types", {}),

    # Tools
    ("tools.get_categories", {}),
    ("tools.get_sources", {}),

    # Templates
    ("templates.get_categories", {}),

    # Agents
    ("agents.list_agents", {}),
]


def call_rpc(method: str, params: dict) -> dict:
    """Call an RPC method and return the response."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }

    result = subprocess.run(
        [sys.executable, "-m", "bridge.main"],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
        timeout=30,
    )

    if result.returncode != 0:
        raise RuntimeError(f"RPC failed: {result.stderr}")

    response = json.loads(result.stdout.strip())
    return response


def generate_snapshots():
    """Generate snapshots for all RPC methods."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    results = {"success": [], "failed": []}

    for method, params in RPC_METHODS:
        print(f"Generating snapshot for {method}...", end=" ")
        try:
            response = call_rpc(method, params)

            # Save the full response
            snapshot_file = SNAPSHOTS_DIR / f"{method.replace('.', '_')}.json"
            snapshot_file.write_text(json.dumps(response, indent=2))

            # Check for errors in response
            if "error" in response:
                print(f"ERROR: {response['error']['message']}")
                results["failed"].append((method, response["error"]["message"]))
            else:
                print("OK")
                results["success"].append(method)

        except Exception as e:
            print(f"FAILED: {e}")
            results["failed"].append((method, str(e)))

    # Summary
    print(f"\n{'='*50}")
    print(f"Success: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")

    if results["failed"]:
        print("\nFailed methods:")
        for method, error in results["failed"]:
            print(f"  - {method}: {error}")

    return len(results["failed"]) == 0


if __name__ == "__main__":
    success = generate_snapshots()
    sys.exit(0 if success else 1)
