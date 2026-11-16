#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
dataset="${1:-nested}"
case "$dataset" in
    minimal|multiple|nested) ;;
    *) echo "Usage: demo/run.sh [minimal|multiple|nested] [--headless]" >&2
       exit 2 ;;
esac
if [ "$#" -gt 0 ]; then shift; fi
scenario=stage3
if [ "$dataset" = nested ]; then scenario=stage5; fi
python3 -m examples.make_vfs "$dataset"
DEMO_PATH=/ exec ./run.sh --vfs "examples/generated/$dataset.zip" \
    --script "examples/startup/$scenario.txt" "$@"
