from __future__ import annotations

import sys

from f1se.cli_router import dispatch
from f1se.cli_v20 import main as previous_main


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    return dispatch(args, previous_main)
