"""Repo location and the frozen YAML configuration.

`config/experiment.yaml` is the single source of truth. Nothing in `src/` hardcodes
an experimental number.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_ROOT_MARKERS = ("pyproject.toml", "config")
_MERGE_SCRIPT = Path("examples/scripts/utils/merge_weights.py")


def project_root(start: Path | None = None) -> Path:
    """Walk up until the repo root is found.

    Notebooks live in a subdirectory and also run on Colab, so no call site can rely
    on the working directory. Colab sessions typically start at ``/content``, which
    has neither ``pyproject.toml`` nor a parent that does — if no markers are found,
    use the starting directory (the same fallback as ``Path.cwd()``).
    """
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if all((candidate / marker).exists() for marker in _ROOT_MARKERS):
            return candidate
    return here


def bootstrap(start: Path | None = None) -> Path:
    """Put `src/` on sys.path so notebooks work without `pip install -e .`."""
    root = project_root(start)
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    return root


def is_colab() -> bool:
    try:
        import google.colab  # noqa: F401
    except ImportError:
        return False
    return True


def ahn_repo(explicit: Path | str | None = None) -> Path:
    """Resolve the ByteDance-Seed/AHN checkout used for weight merging.

    Order: explicit path → ``AHN_REPO`` env → Colab ``/content/AHN`` →
    ``vendor/AHN`` under this project.
    """
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(Path(explicit).expanduser())
    if env := os.environ.get("AHN_REPO"):
        candidates.append(Path(env).expanduser())
    if is_colab():
        candidates.append(Path("/content/AHN"))
    candidates.append(project_root() / "vendor" / "AHN")

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if (resolved / _MERGE_SCRIPT).is_file():
            return resolved

    searched = ", ".join(str(p) for p in seen) or "(none)"
    raise FileNotFoundError(
        "AHN repo not found (need examples/scripts/utils/merge_weights.py). "
        f"Tried: {searched}. "
        "Local: git clone https://github.com/ByteDance-Seed/AHN.git vendor/AHN. "
        "Colab: clone to /content/AHN. Or set AHN_REPO."
    )


@lru_cache(maxsize=None)
def _load(relative_path: str) -> dict[str, Any]:
    path = project_root() / relative_path
    with path.open() as handle:
        loaded = yaml.safe_load(handle)
    if loaded is None:
        raise ValueError(f"{relative_path} is empty.")
    return loaded


def clear_caches() -> None:
    """Drop cached YAML (call after editing config/*.yaml or on notebook reload)."""
    _load.cache_clear()


def experiment() -> dict[str, Any]:
    return _load("config/experiment.yaml")


def facts() -> dict[str, Any]:
    return _load("config/facts.yaml")


def run_mode(name: str = "pilot") -> dict[str, Any]:
    return experiment()["run_modes"][name]


def pilot_pass2() -> dict[str, Any]:
    """Frozen Pilot Pass 2 design block (model-tat-targeted grid)."""
    return experiment()["pilot_pass2"]


def load_pass2_calibration() -> dict[str, Any]:
    """Per-fact-type requested->model-tat calibration built by the dry run."""
    import json

    path = project_root() / pilot_pass2()["calibration_file"]
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found. Run scripts/pilot_pass2_dryrun.py first "
            "(no model; needs the Qwen2.5 tokenizer)."
        )
    return json.loads(path.read_text())


def final() -> dict[str, Any]:
    """Frozen final inferential design block (protocol/final_experiment_design.md)."""
    return experiment()["final"]


def load_final_calibration() -> dict[str, Any]:
    """Per-fact-type requested->model-tat calibration for the final grid."""
    import json

    path = project_root() / final()["calibration_file"]
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found. Run scripts/full_run_dryrun.py first "
            "(no model; needs the Qwen2.5 tokenizer)."
        )
    return json.loads(path.read_text())


def final_manifest() -> dict[str, Any]:
    """The frozen-design manifest/hash (config/final_design_manifest.json)."""
    import json

    path = project_root() / final()["manifest_file"]
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found. Run scripts/full_run_dryrun.py --manifest."
        )
    return json.loads(path.read_text())


def prompt_hash() -> str:
    """SHA-256 over the frozen prompt template + per-type answer hints.

    The manifest pins this so a silent edit to `dataset._PROMPT` or a
    `config/facts.yaml` `answer_hint` is caught before the final run.
    """
    import hashlib

    from ahnexp import dataset  # local import: dataset imports config

    hints = facts()["types"]
    payload = dataset._PROMPT + "\x1e" + "\x1e".join(
        f"{name}:{entry.get('answer_hint', '')}" for name, entry in sorted(hints.items())
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(relative_path: str) -> str:
    """SHA-256 of a repo file, for manifest integrity checks."""
    import hashlib

    return hashlib.sha256((project_root() / relative_path).read_bytes()).hexdigest()


def output_path(key: str, mode: str = "pilot") -> Path:
    """Resolve `outputs.raw`, substituting the run-mode suffix."""
    template = experiment()["outputs"][key]
    path = project_root() / template.format(suffix=run_mode(mode)["suffix"])
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def figure_path(name: str, mode: str = "pilot") -> Path:
    root = project_root() / experiment()["outputs"]["figures"]
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{name}{run_mode(mode)['suffix']}.png"


def table_path(name: str, mode: str = "pilot") -> Path:
    root = project_root() / experiment()["outputs"]["tables"]
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{name}{run_mode(mode)['suffix']}.md"


# ---------------------------------------------------------------------------
# The H2 threshold gate
# ---------------------------------------------------------------------------

def tokens_per_fact() -> float:
    """Conversion between the fact-denominated threshold and the token axis."""
    conversion = experiment()["threshold"]["tokens_per_fact"]
    return float(conversion["measured"] or conversion["estimate"])


def compression_threshold(strict: bool = True) -> int:
    """The deprecated 50-fact / 768-token reference, in model tokens.

    DEPRECATED 2026-09-04: the `50 facts x 15.37` derivation is unsupported (the
    cited Khandelwal et al. 2018 reports ~50 *tokens* of LSTM order sensitivity, not
    a 50-fact AHN saturation threshold). H2 no longer depends on it — see
    `protocol/h2_threshold_decision_2026-09-04.md`.

    `strict=True` still raises (status is never LOCKED): the 768 number must not
    reach an H2 table. `strict=False` still returns the derived value, used only as
    the legacy `mini` pressure-grid backstop, never as an H2 reference line.
    """
    threshold = experiment()["threshold"]
    if strict and threshold.get("status") != "LOCKED":
        raise ValueError(
            "The H2 threshold T (50-fact / 768-token derivation) is DEPRECATED and "
            f"unsupported — see {threshold['decision_record']} and "
            "protocol/h2_threshold_decision_2026-09-04.md. H2 is operationalised "
            "without it; do not lock or cite this value."
        )

    tokens = threshold.get("tokens")
    if tokens is None:
        facts_value = threshold.get("facts")
        if facts_value is None:
            raise ValueError("Threshold has neither `tokens` nor `facts`.")
        tokens = round(float(facts_value) * tokens_per_fact())
    return int(tokens)


def assert_threshold_clears_window(sliding_window: int) -> None:
    """T must sit outside the lossless window, or there is no compression to test.

    Below one window the target is still in the exact KV cache and every arm,
    including the no-AHN baseline, sits at ceiling.
    """
    minimum = float(experiment()["threshold"]["min_windows"])
    tokens = compression_threshold(strict=False)
    windows = tokens / sliding_window
    if windows < minimum:
        raise ValueError(
            f"T = {tokens} tokens is only {windows:.2f} sliding windows "
            f"({sliding_window} tokens each), below the required {minimum}. The target "
            "would still be in the lossless KV cache, so the experiment would measure "
            "nothing. Shorten the window or re-derive T."
        )
