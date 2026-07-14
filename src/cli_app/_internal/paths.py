"""Cross-platform path resolution helpers.

Kept deliberately small: anything that needs to compute a path for the
splitter or reconciler engines goes through this module so the ``pathlib``
and ``encoding`` rules from ``AGENTS.md`` are honoured in one place.
"""

from __future__ import annotations

from pathlib import Path


def package_dir_for(source: Path, output_dir: Path | None) -> Path:
    """Compute the proposed package directory for splitting a source file.

    If ``output_dir`` is ``None``, the package lives next to the source
    file (``source.parent / source.stem``). Otherwise the package lives
    inside ``output_dir`` (``output_dir / source.stem``).

    This function does not check whether the returned path already exists;
    the caller is responsible for surfacing a :class:`FileExistsError` to
    the user with a clear error message.

    Args:
        source: The path to the source Python file.
        output_dir: An optional parent directory for the new package.

    Returns:
        The proposed package directory path. The directory may or may not
        already exist on disk.
    """
    base = output_dir if output_dir is not None else source.parent
    return base / source.stem
