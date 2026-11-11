# SPDX-License-Identifier: GPL-3.0-or-later
"""Reading and writing a pie file on disk."""

import os
import time

from . import model


def load(path):
    """Return (pies, problem) for the pie file at path.

    A missing file is no pies and no problem. A file that cannot be read as
    pies is moved aside, because the next save would overwrite it.
    """
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return (), None
    except OSError as error:
        return (), f"{path.name} could not be opened: {error}"
    try:
        return model.loads(raw.decode("utf-8")), None
    except UnicodeDecodeError:
        reason = "not UTF-8 text"
    except model.InvalidPieFile as error:
        reason = str(error)
    kept = path.with_name(
        f"{path.stem}.invalid-{time.strftime('%Y%m%d-%H%M%S')}{path.suffix}"
    )
    os.replace(path, kept)
    return (), f"{path.name} was not loaded and is kept as {kept.name}: {reason}"


def save(path, pies):
    """Write pies to path so that a crash leaves the old file or the new one."""
    text = model.dumps(pies)
    temporary = path.with_name(path.name + ".tmp")
    with open(temporary, "w", encoding="utf-8") as file:
        file.write(text)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary, path)
