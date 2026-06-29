#!/bin/bash -eux

PLATFORM_ROOT="$(dirname "$(dirname "$(greadlink -f "${BASH_SOURCE[0]}")")")"
UNGOOGLED_REPO=$PLATFORM_ROOT/helium-chromium

"$UNGOOGLED_REPO/devutils/check_patch_files.py" -p "$PLATFORM_ROOT/patches"
