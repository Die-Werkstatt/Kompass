#!/bin/sh
# Builds kompass-<version>.zip in this folder.
# With "install" it also installs and enables it in the user_default repository.
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

if [ "${1:-}" = install ]; then
    # An open Blender drops the new extension from the preferences it saves.
    if pgrep -xi blender >/dev/null 2>&1; then
        echo "Close Blender and run this again." >&2
        exit 1
    fi
    version=$(sed -n 's/^version = "\(.*\)"/\1/p' kompass/blender_manifest.toml)
    "$blender" --command extension install-file -r user_default --enable "kompass-$version.zip"
fi
