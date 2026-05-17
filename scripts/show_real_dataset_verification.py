"""Display documented real dataset verification summary.

This script reads logs/real_dataset_test_summary.json and prints the documented
verification scope. It does not execute experiments, call runtime code, or modify
any project data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = PROJECT_ROOT / "logs" / "real_dataset_test_summary.json"


def load_summary() -> dict[str, Any]:
    with SUMMARY_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    if not SUMMARY_PATH.exists():
        print(f"[WARN] Verification summary not found: {SUMMARY_PATH.relative_to(PROJECT_ROOT).as_posix()}")
        return 0

    summary = load_summary()
    print("SKTAQ Real Dataset Verification Summary")
    print("=" * 40)
    print(f"Purpose: {summary.get('purpose', 'documented verification summary')}")
    print(f"Runtime effect: {summary.get('runtime_effect', 'none')}")
    print()

    for item in summary.get("datasets", []):
        workflow = " -> ".join(item.get("tested_workflow", []))
        print(f"Dataset: {item.get('dataset', 'unknown')}")
        print(f"Source: {item.get('source', 'not specified')}")
        print(f"Expected path: {item.get('expected_path', 'not specified')}")
        print(f"Index: {item.get('index', 'not specified')}")
        print(f"Encryption: {item.get('encryption', 'not specified')}")
        print(f"Key size: {item.get('key_size', 'not specified')}")
        print(f"Query mode: {item.get('query_mode', 'not specified')}")
        print(f"Workflow: {workflow}")
        print(f"Status: {item.get('status', 'documented')}")
        print("-" * 40)

    print("[INFO] This display script does not run real tests or modify the SKTAQ system.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
