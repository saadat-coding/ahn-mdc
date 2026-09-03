#!/usr/bin/env bash
# =============================================================================
# Kaggle environment for the observe-only AHN window diagnostic (Task #1).
# ENVIRONMENT ONLY — no experimental methodology, model code, dataset, scoring,
# metrics, window=256, or Juan-approved matched config is touched here.
#
# Failure history
#  (1) Kaggle's torch 2.10 / cu128 has no prebuilt flash-attn wheel, so pip built
#      it from source -> nvcc jobs x ~8 GB -> 30 GB session OOM -> kernel restart.
#  (2) Pinning torch 2.6.0 from the cu124 index gave the manylinux2014 /
#      CXX11-ABI-FALSE build. The Dao-AILab flash-attn torch2.6 wheels are
#      compiled against CXX11-ABI-TRUE torch (verified: both the abiFALSE- and
#      abiTRUE-labelled wheels carry the identical all-`__cxx11` undefined c10
#      symbol set — the abiFALSE label is a Dao packaging bug), so the wheel
#      failed at dlopen: `undefined symbol: _ZN3c105ErrorC2ENS_14SourceLocation
#      ENSt7__cxx11...` (c10::Error::Error(SourceLocation, std::__cxx11::string)).
#
# Fix
#   torch 2.6.0 from the cu126 index -> manylinux_2_28 = CXX11-ABI-TRUE, whose
#   libc10.so DOES export that symbol (verified). transformers stays 4.51.0.
#   The prebuilt flash-attn cp3xx torch2.6 abiTRUE wheel is installed by URL.
#   Nothing is compiled.
#
#   flash-attn 2.x kernels are sm_80+ ONLY (`TORCH_CHECK(cc_major>=8,
#   "FlashAttention only supports Ampere GPUs or newer")`; the wheels ship
#   sm_80/sm_90 SASS, no PTX). Kaggle T4 (sm_75) and P100 (sm_60) CANNOT run it.
#   USE THE KAGGLE **L4** ACCELERATOR (sm_89). The fail-fast check enforces this.
#
# REQUIRES A FRESH KAGGLE SESSION.
#
# Settings: Accelerator = GPU **L4** · Internet = On · Persistence = Files only.
# =============================================================================
set -euo pipefail

REPO="${AHNEXP_ROOT:-/kaggle/working/ahn-mdc}"
AHN_DIR="${AHN_REPO:-/kaggle/working/AHN}"
# SETUP_PY lets the caller target a specific interpreter — e.g. an isolated
# Python 3.12 venv on Colab, whose runtime kernel is 3.13. Unset => the ambient
# `python` (Kaggle). All installs go through "$PY -m pip".
PY="${SETUP_PY:-$(command -v python)}"
PIP_INSTALL="$PY -m pip install --disable-pip-version-check --no-cache-dir -q"

FA_VER="2.8.3.post1"
FA_TORCH_TAG="torch2.6"            # flash-attn wheels are tagged by torch minor
TORCH_VER="2.6.0"
SUPPORTED_PYTAGS="cp311 cp312"     # Dao-AILab publishes torch2.6 wheels for both

PYTAG="$($PY -c 'import sys;print(f"cp{sys.version_info[0]}{sys.version_info[1]}")')"
case " ${SUPPORTED_PYTAGS} " in
  *" ${PYTAG} "*) echo "== python ${PYTAG} (supported)" ;;
  *)
    echo "SETUP FAILED: Kaggle Python is ${PYTAG}; supported tags: ${SUPPORTED_PYTAGS}."
    echo "Dao-AILab flash-attn ${FA_VER} publishes prebuilt ${FA_TORCH_TAG} wheels only for those."
    exit 1
    ;;
esac

# cu126 (manylinux_2_28) — NOT cu124. The flash-attn ${FA_TORCH_TAG} wheels are
# compiled against CXX11-ABI-TRUE torch: BOTH the abiFALSE- and abiTRUE-labelled
# wheels have byte-identical, all-`__cxx11` undefined c10 symbols
# (verified: c10::Error::Error(SourceLocation, std::__cxx11::string)) — the
# abiFALSE label is a Dao-AILab packaging bug. torch 2.6.0+cu124 is the
# manylinux2014 / CXX11-ABI-FALSE build, whose libc10.so exports the OLD-ABI
# std::string variant, so the wheel fails at dlopen with
# `undefined symbol: _ZN3c105ErrorC2ENS_14SourceLocationENSt7__cxx11...`.
# torch 2.6.0+cu126 (manylinux_2_28) IS CXX11-ABI-TRUE and exports the symbol.
TORCH_INDEX="https://download.pytorch.org/whl/cu126"

echo "== 1/6  pin torch (torch ${TORCH_VER} / cu126 manylinux_2_28 = CXX11-ABI-TRUE; no compile)"
$PIP_INSTALL "torch==${TORCH_VER}" --index-url "$TORCH_INDEX"

# torchvision / torchaudio: NOT used by fla / flash_attn / ahn / the diagnostic.
# For torch 2.6 the cu126 index only has the OLD-tag (CXX11-ABI-FALSE) 0.21.0 /
# 2.6.0 wheels, which would re-trigger `operator torchvision::nms does not exist`
# against the ABI-TRUE torch. Remove Kaggle's torch-2.10 copies so a stray import
# fails cleanly (ModuleNotFoundError) instead of with an undefined symbol.
$PY -m pip -q uninstall -y torchvision torchaudio >/dev/null 2>&1 || true

ABI="$($PY -c 'import torch;print("TRUE" if torch.compiled_with_cxx11_abi() else "FALSE")')"
if [ "$ABI" != "TRUE" ]; then
  echo "SETUP FAILED: torch reports cxx11abi=${ABI}, but the flash-attn ${FA_TORCH_TAG} wheels"
  echo "require CXX11-ABI-TRUE torch. pip pulled a non-manylinux_2_28 build — check ${TORCH_INDEX}."
  exit 1
fi

TRITON_VER="$($PY -c 'import triton;print(triton.__version__)' 2>/dev/null || true)"
CONSTRAINTS=/tmp/ahn_constraints.txt
{
  echo "torch==${TORCH_VER}"
  echo "transformers==4.51.0"
  [ -n "${TRITON_VER}" ] && echo "triton==${TRITON_VER}"
} > "$CONSTRAINTS"
echo "   constraints (nothing below may move these):"
sed 's/^/     /' "$CONSTRAINTS"

echo "== 2/6  transformers 4.51.0 (AHN modeling target — do not change)"
$PIP_INSTALL -c "$CONSTRAINTS" "transformers==4.51.0"

echo "== 3/6  flash-attn ${FA_VER} — PREBUILT wheel for torch ${TORCH_VER} / ${PYTAG} / cxx11abi=${ABI} (no source build)"
FA_WHL="flash_attn-${FA_VER}+cu12${FA_TORCH_TAG}cxx11abi${ABI}-${PYTAG}-${PYTAG}-linux_x86_64.whl"
FA_URL="https://github.com/Dao-AILab/flash-attention/releases/download/v${FA_VER}/${FA_WHL}"
echo "   ${FA_URL}"
FA_HTTP="$(curl -o /dev/null -sIL -w '%{http_code}' "$FA_URL" || echo 000)"
if [ "$FA_HTTP" != "200" ]; then
  echo "SETUP FAILED: no matching prebuilt flash-attn wheel (HTTP ${FA_HTTP})."
  echo "Refusing to build flash-attn from source (that is what exhausted the session last time)."
  exit 1
fi
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
# numpy / pandas: `import ahnexp` needs them; a no-op on Kaggle (preinstalled),
# required in a fresh Colab venv.
$PIP_INSTALL -c "$CONSTRAINTS" numpy pandas pyyaml jinja2 pyarrow accelerate

echo
echo "== fail-fast import check (fresh interpreter) =="
$PY - <<'PYCHECK'
import importlib, sys
bad = []
print(f"  interpreter {sys.executable}  Python {sys.version.split()[0]}")
if sys.version_info[:2] not in ((3, 11), (3, 12)):
    bad.append(f"interpreter is Python {sys.version_info[0]}.{sys.version_info[1]} "
               "(need 3.11 or 3.12 — the prebuilt flash-attn wheels)")
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
    if not torch.compiled_with_cxx11_abi():
        bad.append("torch is not CXX11-ABI-TRUE (need the cu126 manylinux_2_28 build)")
    if transformers.__version__ != "4.51.0":
        bad.append(f"transformers=={transformers.__version__} (want 4.51.0)")
    if torch.cuda.is_available():
        cap = torch.cuda.get_device_capability()
        name = torch.cuda.get_device_name(0)
        print(f"  GPU  {name}  sm_{cap[0]}{cap[1]}")
        if cap[0] < 8:
            bad.append(f"GPU {name} is sm_{cap[0]}{cap[1]} — flash-attn 2.x needs sm_80+ "
                       "(Ampere/Ada/Hopper). Kaggle T4 (sm_75) and P100 (sm_60) FAIL every "
                       "flash_attn_func call. Select the L4 accelerator.")
    else:
        bad.append("no CUDA GPU visible")
except Exception as e:
    bad.append(f"version/gpu check: {e}")
if bad:
    print("\nSETUP FAILED:", bad)
    print("Do NOT proceed. Fix the item(s) above in a fresh Kaggle session.")
    sys.exit(1)
print("\nimports OK")
PYCHECK

echo
echo "SETUP OK (torch ${TORCH_VER} cxx11abi=${ABI}, flash-attn ${FA_VER} prebuilt, ${PYTAG}). Now, in order:"
echo "  1) Run -> Restart & clear cell outputs        (mandatory: torch was replaced on disk)"
echo "  2) run the ENV VERIFICATION cell"
echo "  3) run the DIAGNOSTIC cell"
