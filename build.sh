#!/bin/sh
# Builds kompass-<version>.zip in this folder. Does not install it.
set -eu
cd "$(dirname "$0")"

blender=${BLENDER:-}
if [ -z "$blender" ]; then
    if command -v blender >/dev/null 2>&1; then
        blender=blender
    elif [ -x /Applications/Blender.app/Contents/MacOS/Blender ]; then
        blender=/Applications/Blender.app/Contents/MacOS/Blender
    else
        echo "Blender was not found. Set BLENDER to its path and run this again." >&2
        exit 1
    fi
fi

"$blender" --command extension build --source-dir kompass
