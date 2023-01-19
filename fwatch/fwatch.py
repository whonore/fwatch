#!/usr/bin/env python3
import argparse
import shlex
import subprocess
import sys
import time
from collections import defaultdict as ddict
from pathlib import Path
from typing import DefaultDict, Iterable, Sequence

from pathspec import PathSpec

IGNORE = (".git", ".github")
DEFAULT_POLL_RATE_MS = 1000


def log(msg: str) -> None:
    print(f"[fwatch] {msg}", file=sys.stderr)


def ignorelist(gitignore: str | Path | None) -> tuple[PathSpec, Path | None]:
    ignore = PathSpec.from_lines("gitwildmatch", IGNORE)
    ignore_root = None
    if gitignore is not None:
        with open(gitignore, "r", encoding="utf-8") as f:
            ignore += PathSpec.from_lines("gitwildmatch", f)
            ignore_root = Path(gitignore).resolve().parent
    return ignore, ignore_root


def collect_files(
    paths: Iterable[str | Path],
    ignore: PathSpec,
    ignore_root: Path | None = None,
) -> list[Path]:
    ps = []
    for p in (
        Path(p).resolve().relative_to(ignore_root)
        if ignore_root is not None
        else Path(p).resolve()
        for p in paths
    ):
        if ignore.match_file(p):
            continue
        if p.is_dir():
            ps += collect_files(p.iterdir(), ignore)
        else:
            ps.append(p)
    return ps


def do_update(on_update: str, update_cmd: Sequence[str]) -> None:
    log(f"RUNNING: {on_update}")
    try:
        subprocess.run(update_cmd, check=True)
    except subprocess.CalledProcessError:
        log("FAILED")


def watch(
    paths: Sequence[str | Path],
    /,
    on_update: str | None = None,
    poll_rate: int = DEFAULT_POLL_RATE_MS,
    gitignore: str | Path | None = None,
) -> None:
    ignore, ignore_root = ignorelist(gitignore)
    update_cmd = None if on_update is None else shlex.split(on_update)
    mtimes: DefaultDict[Path, float] = ddict(float)
    while True:
        changed = False
        for f in collect_files(paths, ignore, ignore_root):
            mtime = f.stat().st_mtime
            if mtime > mtimes[f]:
                log(f"CHANGED: {f}")
                mtimes[f] = mtime
                changed = True
        if changed and on_update is not None:
            assert update_cmd is not None
            do_update(on_update, update_cmd)
        time.sleep(poll_rate / 1000)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--poll-rate",
        default=DEFAULT_POLL_RATE_MS,
        help="how often to check for changes (ms)",
    )
    parser.add_argument(
        "-u",
        "--on-update",
        default=None,
        help="the command to run when a file changes",
    )
    parser.add_argument(
        "-g",
        "--gitignore",
        default=None,
        help="the path to a .gitignore file to use",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="paths to watch",
    )
    args = parser.parse_args()

    try:
        watch(
            args.paths,
            on_update=args.on_update,
            poll_rate=args.poll_rate,
            gitignore=args.gitignore,
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
