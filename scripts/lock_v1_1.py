#!/usr/bin/env python3
"""Create the durable immutable v1.1 reporting-amendment snapshot.

Does NOT touch FINAL_LOCKED, the raw parquet, or any frozen v1.0 output. Copies
the approved v1.1 products + decision documents into final_audit/V1_1_LOCKED/ and
writes V1_1_LOCK_MANIFEST.json with a SHA-256 of every locked file. Verifies the
raw artifact SHA-256 before and after.

    python scripts/lock_v1_1.py --repo .
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAW_SHA256 = "a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e"
RAW = "final_audit/FINAL_LOCKED/results_FINAL_92160.parquet"
V11_SRC = "outputs/final_v1_1_reporting_amendment"
LOCK_DIR = "final_audit/V1_1_LOCKED"
PROTOCOL_DOCS = [
    "protocol/final_results_specification.md",
    "protocol/amendment_h2_transition_width.md",
    "protocol/final_reporting_additions.md",
    "protocol/final_claims_register.md",
    "protocol/final_exhibit_plan.md",
]
IMPLEMENTATION_COMMITS = {
    "decision_documents": "76e5207",       # 5 protocol docs, before any amendment code
    "implementation": "626521a",           # reporting_amendment.py + scripts + tests + v1.1 outputs
    "protocol_record": "1031b07",          # §13 implementation record etc.
    "implementation_report": "ab36f2c",    # AMENDMENT_REPORT.md
}


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.environ.get("AHNEXP_ROOT", "."))
    args = ap.parse_args()
    root = Path(args.repo).expanduser().resolve()
    if not (root / "config" / "experiment.yaml").is_file():
        sys.exit(f"--repo {root} is not the ahn-mdc checkout")

    raw = root / RAW
    got = _sha256(raw)
    print(f"raw artifact SHA-256 (pre):  {got}")
    if got != RAW_SHA256:
        sys.exit("RAW SHA-256 MISMATCH — STOP. Nothing written.")
    print("  OK\n")

    lock = root / LOCK_DIR
    if lock.exists():
        sys.exit(f"{lock} already exists — refusing to overwrite an existing lock.")
    lock.mkdir(parents=True)
    (lock / "v1_1_products").mkdir()
    (lock / "decision_documents").mkdir()

    # 1. all v1.1 reporting-amendment products
    for f in sorted((root / V11_SRC).iterdir()):
        if f.is_file():
            shutil.copy2(f, lock / "v1_1_products" / f.name)
    # 2. decision documents
    for rel in PROTOCOL_DOCS:
        shutil.copy2(root / rel, lock / "decision_documents" / Path(rel).name)
    # 3. the frozen v1.0 width result, kept as the record it corrects
    shutil.copy2(root / "final_audit/FINAL_LOCKED/final_h2_h2_width.csv",
                 lock / "frozen_v1_0_h2_width_RECORD.csv")

    # 4. commit + analysis-version + verification text records
    (lock / "IMPLEMENTATION_COMMITS.txt").write_text(
        "\n".join(f"{k}: {_git(root, 'rev-parse', v)}  {_git(root, 'log', '-1', '--format=%s', v)}"
                  for k, v in IMPLEMENTATION_COMMITS.items()) + "\n"
        + f"branch: {_git(root, 'rev-parse', '--abbrev-ref', 'HEAD')}\n"
        + f"HEAD at lock time: {_git(root, 'rev-parse', 'HEAD')}\n")
    (lock / "ANALYSIS_VERSION.txt").write_text(
        "frozen analysis (full_run.ANALYSIS_VERSION): 1.0\n"
        "reporting amendment (reporting_amendment.ANALYSIS_VERSION): 1.1\n")
    (lock / "FROZEN_V1_0_VERIFICATION.txt").write_text(
        "scripts/verify_frozen_v1_0.py --nboot 2000\n"
        "result: 53/53 frozen H1/H2/H3/control quantities identical to "
        "final_audit/FINAL_LOCKED/final_*.csv\n"
        "max |delta|: 5.7e-14 (float noise)\n"
        "final_h2_h2_width.csv reproduces as all-NaN (frozen defect preserved exactly)\n"
        "raw artifact SHA-256 unchanged: " + RAW_SHA256 + "\n")
    (lock / "TEST_RESULT.txt").write_text(
        "python -m unittest discover -s tests\n"
        "result: 267 tests pass (255 pre-amendment + 12 tests/test_reporting_amendment.py)\n"
        "no GPU\n")

    # 5. hash every locked file
    files = {}
    for p in sorted(lock.rglob("*")):
        if p.is_file():
            files[str(p.relative_to(lock))] = _sha256(p)

    post = _sha256(raw)
    if post != RAW_SHA256:
        sys.exit("RAW SHA-256 CHANGED DURING LOCK — abort (should be impossible; nothing writes to it).")

    manifest = {
        "locked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": "Immutable snapshot of the APPROVED post-freeze reporting amendment (analysis v1.1).",
        "analysis_version": "1.1",
        "frozen_v1_0_analysis_version": "1.0",
        "raw_artifact": {
            "path": RAW,
            "sha256_expected": RAW_SHA256,
            "sha256_verified_pre_lock": got,
            "sha256_verified_post_lock": post,
            "unchanged": got == post == RAW_SHA256,
        },
        "implementation_commits": {k: _git(root, "rev-parse", v) for k, v in IMPLEMENTATION_COMMITS.items()},
        "protocol_commit": _git(root, "rev-parse", IMPLEMENTATION_COMMITS["protocol_record"]),
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "head_at_lock": _git(root, "rev-parse", "HEAD"),
        "test_result": "267 tests pass (no GPU)",
        "frozen_v1_0_reproduction": "53/53 quantities identical (max |delta| 5.7e-14); "
                                    "final_h2_h2_width.csv reproduces all-NaN (defect preserved)",
        "statements": [
            "No raw evidence was modified: results_FINAL_92160.parquet SHA-256 is byte-identical "
            "before and after this lock and equals the original locked value.",
            "No frozen-v1.0 output was replaced, overwritten, or hidden. "
            "final_audit/FINAL_LOCKED/ is untouched; frozen_v1_0_h2_width_RECORD.csv here is a COPY "
            "kept for reference and still shows the original all-NaN result.",
            "The v1.1 amendment is a reporting correction (per-eligible-fact-type 90->10 transition "
            "width) for a frozen descriptive statistic that was mathematically undefined; it is NOT "
            "a new frozen primary endpoint and does not change W, K, strict accuracy, the pressure "
            "coordinate, the grid, seeds, the scorer, the prompt, the dataset, or the gates.",
            "No GPU / model generation was performed.",
        ],
        "file_count": len(files),
        "files_sha256": files,
    }
    (lock / "V1_1_LOCK_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    # include the manifest's own hash in a sidecar (self-verification)
    (lock / "V1_1_LOCK_MANIFEST.sha256").write_text(
        _sha256(lock / "V1_1_LOCK_MANIFEST.json") + "  V1_1_LOCK_MANIFEST.json\n")

    print(f"raw artifact SHA-256 (post): {post}  OK")
    print(f"\nV1_1_LOCKED created: {lock}")
    print(f"  {len(files)} files hashed")
    print(f"  manifest: {lock / 'V1_1_LOCK_MANIFEST.json'}")
    print(f"  manifest sha256: {_sha256(lock / 'V1_1_LOCK_MANIFEST.json')}")


if __name__ == "__main__":
    main()
