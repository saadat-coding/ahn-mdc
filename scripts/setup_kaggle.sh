#!/usr/bin/env bash
# =============================================================================
# Kaggle environment for the observe-only AHN window diagnostic (Task #1).
# ENVIRONMENT ONLY — no experimental methodology, model code, dataset, scoring,
# metrics, window=256, or Juan-approved matched config is touched here.
#
# Why the previous run died
#   Kaggle ships torch 2.10.0 / cu128. Dao-AILab publishes prebuilt flash-attn
#   wheels for torch 2.4..2.8 ONLY — none for 2.9/2.10. `pip install flash-attn`
#   therefore built from source; its setup.py spawns one nvcc job per CPU
#   (~8 GB RAM each), which exhausted the 30 GB session and forced a kernel
#   restart, leaving torch/torchvision ABI-mismatched
#   (`RuntimeError: operator torchvision::nms does not exist`) and fla / flash_attn
#   / ahn.* unimportable.
#
# Smallest reproducible fix
#   Pin the torch stack to a version flash-attn ships a *prebuilt* wheel for:
#   torch 2.6.0 / torchvision 0.21.0 / cu124  (AHN's documented stack is
#   torch 2.5.1 / CUDA 12.4; the frozen Seerkfang fla fork is from Mar 2025).
#   Install the prebuilt flash-attn wheel by URL. Nothing is compiled.
#   transformers stays pinned at 4.51.0 (AHN modeling target).
#
# REQUIRES A FRESH KAGGLE SESSION (Factory reset / brand-new notebook). A kernel
# restart does NOT undo the corrupted on-disk packages from the failed run.
#
# Settings: Accelerator = GPU (2x T4) · Internet = On · Persistence = Files only.
# =============================================================================
set -euo pipefail

REPO="${AHNEXP_ROOT:-/kaggle/working/ahn-mdc}"
AHN_DIR="${AHN_REPO:-/kaggle/working/AHN}"
PY="$(command -v python)"
PIP_INSTALL="$PY -m pip install --disable-pip-version-check --no-cache-dir -q"

FA_VER="2.8.3.post1"
TORCH_VER="2.6.0"

PYTAG="$($PY -c 'import sys;print(f"cp{sys.version_info[0]}{sys.version_info[1]}")')"
if [ "$PYTAG" != "cp311" ]; then
  echo "SETUP FAILED: Kaggle Python is ${PYTAG}, but the pinned flash-attn wheel is cp311."
  echo "Use a Kaggle image with Python 3.11."
  exit 1
fi

echo "== 1/6  pin torch stack (torch ${TORCH_VER} / cu124 — has a prebuilt flash-attn wheel; no compile)"
$PIP_INSTALL "torch==${TORCH_VER}" "torchvision==0.21.0" "torchaudio==2.6.0" \
    --index-url https://download.pytorch.org/whl/cu124

TRITON_VER="$($PY -c 'import triton;print(triton.__version__)' 2>/dev/null || true)"
CONSTRAINTS=/tmp/ahn_constraints.txt
{
  echo "torch==${TORCH_VER}"
  echo "torchvision==0.21.0"
  echo "torchaudio==2.6.0"
  echo "transformers==4.51.0"
  [ -n "${TRITON_VER}" ] && echo "triton==${TRITON_VER}"
} > "$CONSTRAINTS"
echo "   constraints (nothing below may move these):"
sed 's/^/     /' "$CONSTRAINTS"

echo "== 2/6  transformers 4.51.0 (AHN modeling target — do not change)"
$PIP_INSTALL -c "$CONSTRAINTS" "transformers==4.51.0"

echo "== 3/6  flash-attn ${FA_VER} — PREBUILT wheel matching torch ${TORCH_VER} + this ABI (no source build)"
ABI="$($PY -c 'import torch;print("TRUE" if torch.compiled_with_cxx11_abi() else "FALSE")')"
FA_WHL="flash_attn-${FA_VER}+cu12torch2.6cxx11abi${ABI}-cp311-cp311-linux_x86_64.whl"
FA_URL="https://github.com/Dao-AILab/flash-attention/releases/download/v${FA_VER}/${FA_WHL}"
echo "   ${FA_URL}"
$PIP_INSTALL --no-deps "$FA_URL"

echo "== 4/6  flash-linear-attention (Seerkfang fork @ main; pure-Python Triton kernels)"
$PIP_INSTALL -c "$CONSTRAINTS" "git+https://github.com/Seerkfang/flash-linear-attention.git@main"
$PIP_INSTALL -c "$CONSTRAINTS" wandb einops

echo "== 5/6  ByteDance AHN package (core only; NOT the [train] extra)"
if [ ! -f "$AHN_DIR/examples/scripts/utils/merge_weights.py" ]; then
  rm -rf "$AHN_DIR"
  git clone --depth 1 https://github.com/ByteDance-Seed/AHN.git "$AHN_DIR"
fi
$PIP_INSTALL --no-deps -e "$AHN_DIR"

echo "== 6/6  project analysis deps"
$PIP_INSTALL -c "$CONSTRAINTS" pyyaml jinja2 pyarrow accelerate

echo
echo "== fail-fast import check (fresh interpreter) =="
$PY - <<'PYCHECK'
import importlib, sys
bad = []
for m in ("torch", "transformers", "triton", "fla", "flash_attn", "ahn.transformer.qwen2_ahn"):
    try:
        mod = importlib.import_module(m)
        print(f"  OK   {m:34} {getattr(mod, '__version__', '')}")
    except Exception as e:
        print(f"  FAIL {m:34} {type(e).__name__}: {e}")
        bad.append(m)
try:
    import torch, transformers
    if not torch.__version__.startswith("2.6."):
        bad.append(f"torch=={torch.__version__} (want 2.6.x)")
    if transformers.__version__ != "4.51.0":
        bad.append(f"transformers=={transformers.__version__} (want 4.51.0)")
except Exception as e:
    bad.append(f"version check: {e}")
if bad:
    print("\nSETUP FAILED:", bad)
    print("Do NOT proceed. Start a fresh Kaggle session and re-run this cell.")
    sys.exit(1)
print("\nimports OK")
PYCHECK

echo
echo "SETUP OK. Now, in order:"
echo "  1) Run -> Restart & clear cell outputs        (mandatory: torch was replaced on disk)"
echo "  2) run the ENV VERIFICATION cell"
echo "  3) run the DIAGNOSTIC cell"
