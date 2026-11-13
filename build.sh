#!/bin/sh
# Builds kompass-<version>.zip and kompass_native-<version>.zip in this folder.
# With "install" it also installs and enables Kompass in the user_default repository.
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

# An open Blender drops the new extension from the preferences it saves.
if [ "${1:-}" = install ] && pgrep -xi blender >/dev/null 2>&1; then
    echo "Close Blender and run this again." >&2
    exit 1
fi

"$blender" --background --factory-startup --python-exit-code 1 --python build.py

if [ "${1:-}" = install ]; then
    version=$(sed -n 's/^version = "\(.*\)"/\1/p' kompass/blender_manifest.toml)
    "$blender" --command extension install-file -r user_default --enable "kompass-$version.zip"
fi
