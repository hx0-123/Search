"""Non-invasive checker for documented real dataset paths.

This script only checks whether expected dataset files and sample files exist.
It does not import data, modify databases, run encryption, build indexes, or
execute SKTAQ query workflows.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DATASETS = [
    ("POI", Path("data/POI/poi.csv")),
    ("SINA", Path("data/SINA/sina.csv")),
    ("roadNet-CA", Path("data/roadNet-CA/roadnet_ca.txt")),
    ("PLI", Path("data/PLI/pli.csv")),
    ("HKU", Path("data/HKU/hku.csv")),
    ("RNCA", Path("data/RNCA/rnca.csv")),
]

SAMPLE_FILES = [
    Path("data/sample/poi_sample.csv"),
    Path("data/sample/sina_sample.csv"),
    Path("data/sample/roadnet_ca_sample.csv"),
    Path("data/sample/pli_sample.csv"),
    Path("data/sample/hku_sample.csv"),
    Path("data/sample/rnca_sample.csv"),
]


def report_file(prefix: str, path: Path, ok_label: str, warn_label: str) -> None:
    absolute_path = PROJECT_ROOT / path
    if absolute_path.exists():
        print(f"[OK] {ok_label}: {path.as_posix()}")
    else:
        print(f"[WARN] {warn_label}: {path.as_posix()}")


def main() -> int:
    print("[INFO] Checking expected real dataset paths...")
    print("[INFO] This script is non-invasive and only performs path checks.")

    for sample_path in SAMPLE_FILES:
        report_file("sample", sample_path, "Sample file found", "Sample file missing")

    for dataset, expected_path in EXPECTED_DATASETS:
        absolute_path = PROJECT_ROOT / expected_path
        if absolute_path.exists():
            print(f"[OK] Full dataset {dataset} found at {expected_path.as_posix()}")
        else:
            print(f"[WARN] Full dataset {dataset} not found at {expected_path.as_posix()}")

    print("[INFO] This check does not affect the SKTAQ runtime workflow.")
    print("[INFO] No database import, encryption, index construction, or query execution was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
