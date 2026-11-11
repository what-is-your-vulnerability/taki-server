"""서버는 엔진 공개 API(taki, taki.service)만 import한다. 엔진 내부가 바뀌어도 서버가 깨지지 않게 지킨다."""

import ast
from importlib.util import find_spec
from pathlib import Path

SERVER = Path(__file__).resolve().parents[1] / "src" / "taki_server"
PUBLIC = {"taki", "taki.service"}


def _engine_imports(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "상대 import는 경계 검사가 읽지 못한다"
            names.add(node.module)
            # `from taki import config`처럼 하위 모듈을 꺼내는 경우도 잡는다.
            if node.module == "taki":
                names |= {f"taki.{a.name}" for a in node.names if find_spec(f"taki.{a.name}")}
    return {n for n in names if n == "taki" or n.startswith("taki.")}


def test_server_imports_only_public_engine():
    bad = {str(p.relative_to(SERVER)): sorted(_engine_imports(ast.parse(p.read_text(encoding="utf-8"))) - PUBLIC)
           for p in SERVER.rglob("*.py")}
    assert {k: v for k, v in bad.items() if v} == {}
