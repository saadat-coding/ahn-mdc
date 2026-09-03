#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Kaggle GPU environment for the AHN window diagnostic (Task #1).
# ENVIRONMENT ONLY — no experimental methodology here.
#
# Run once per Kaggle session, in the FIRST cell, then RESTART the kernel
# (transformers must be pinned before anything imports it):
#
#     !bash /kaggle/working/ahn-mdc/scripts/setup_kaggle.sh
#     # then: Kernel -> Restart & Run All   (or just Restart)
#
# Requires: Kaggle "Internet" enabled, a GPU accelerator (T4 x2 or P100).
# ---------------------------------------------------------------------------
set -euo pipefail

REPO="${AHNEXP_ROOT:-/kaggle/working/ahn-mdc}"
AHN_DIR="${AHN_REPO:-/kaggle/working/AHN}"
PY="$(command -v python)"

echo "== python: $PY"
"$PY" -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda, 'is_available', torch.cuda.is_available())"

# 1. Pin transformers FIRST. AHN's custom modeling was written against 4.51;
#    Kaggle ships something newer and models._ensure_transformers_for_ahn only
#    ever upgrades, never downgrades.
pip -q install "transformers==4.51.0"

# 2. AHN runtime deps. GatedDeltaNet needs the flash-linear-attention fork;
#    qwen2_ahn.py imports `wandb` and torch.nn.attention.flex_attention at module
#    top; its self-attention hardcodes FlashAttention-2 (attn_implementation is
#    ignored by the AHN layers), so flash-attn must be importable for inference.
pip -q install "git+https://github.com/Seerkfang/flash-linear-attention.git@main"
pip -q install wandb einops
pip -q install "flash-attn==2.8.3" --no-build-isolation || \
  echo "!! flash-attn wheel install failed — see diag output; may need a source build or a matching cuXXX wheel index"

# 3. The ByteDance AHN package (weight-merge + custom Qwen2 classes). Core only —
#    NOT the [train] extra (it pins numpy==1.26.4 / tensorflow / deepspeed).
if [ ! -f "$AHN_DIR/examples/scripts/utils/merge_weights.py" ]; then
  rm -rf "$AHN_DIR"
  git clone --depth 1 https://github.com/ByteDance-Seed/AHN.git "$AHN_DIR"
fi
pip -q install -e "$AHN_DIR"

# 4. This project (analysis deps; torch already present on Kaggle).
pip -q install pyyaml jinja2 pyarrow
pip -q install -e "$REPO" || echo "(editable install of ahn-mdc skipped; the diagnostic adds src/ to sys.path anyway)"

echo
echo "== versions after setup"
"$PY" - <<'EOF'
import importlib.metadata as m
for pkg in ("transformers", "tokenizers", "accelerate", "huggingface-hub", "safetensors"):
    try:
        print(f"  {pkg:16} {m.version(pkg)}")
    except Exception as e:
        print(f"  {pkg:16} MISSING ({e})")
for mod in ("fla", "flash_attn", "ahn.transformer.qwen2_ahn"):
    try:
        __import__(mod); print(f"  import {mod:24} OK")
    except Exception as e:
        print(f"  import {mod:24} FAIL: {type(e).__name__}: {e}")
EOF

echo
echo "== DONE. Now RESTART the kernel, then run:  python $REPO/scripts/diag_ahn_window.py"
