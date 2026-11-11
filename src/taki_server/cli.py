"""서버 명령줄 입구. 종료 코드: 0 정상, 3 실행 실패."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import uvicorn
from taki import (
    AgentConfig,
    BudgetExceeded,
    ConfigError,
    ForbiddenPathError,
    LlmCallError,
    LlmFormatError,
    SecretLeft,
    load_config,
)

from taki_server.api.app import API_HOST, create_app
from taki_server.store.repo import make_session_factory, run_next, upgrade_database

POLL_SECONDS = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taki-server", description="TAKI 진단 엔진의 로컬 API와 worker를 돌린다.")
    commands = parser.add_subparsers(dest="command", required=True)
    api = commands.add_parser("api")
    api.add_argument("--port", type=int, default=8000)
    api.add_argument("--config", type=Path)
    worker = commands.add_parser("worker")
    worker.add_argument("--once", action="store_true")
    worker.add_argument("--config", type=Path)
    commands.add_parser("openapi")
    commands.add_parser("db-upgrade")
    return parser


def _service(args) -> int:
    if args.command == "db-upgrade":
        upgrade_database()
        return 0
    if args.command == "openapi":
        print(json.dumps(create_app(None, AgentConfig()).openapi(), ensure_ascii=False, indent=1))
        return 0
    config = load_config(args.config)
    sessions = make_session_factory()
    if args.command == "api":
        uvicorn.run(create_app(sessions, config), host=API_HOST, port=args.port)
        return 0
    while True:
        run = run_next(sessions, config, Path("runs"))
        if run is not None:
            print(f"scan {run.id}: {run.status} (종료 코드 {run.exit_code})")
        if args.once:
            return 0
        if run is None:
            time.sleep(POLL_SECONDS)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _service(args)
    except (ConfigError, ForbiddenPathError, FileNotFoundError, LlmCallError, LlmFormatError, BudgetExceeded,
            SecretLeft) as e:
        print(f"실행 실패: {e}", file=sys.stderr)
        return 3
    except Exception as e:  # noqa: BLE001 - 예상 못 한 실패도 실행 실패(3)로 끝낸다.
        print(f"실행 실패: {type(e).__name__}: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
