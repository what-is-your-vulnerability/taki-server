# taki-server

TAKI 진단 엔진(`taki`)을 감싸 검사 대기열·결과 저장·HTTP API를 제공하는 서버다.
API는 검사를 대기열에 넣기만 하고, worker가 엔진으로 검사를 돌려 PostgreSQL에 결과를 남긴다.

## 준비

```bash
docker compose -f deploy/docker-compose.yml up -d --wait   # PostgreSQL만 127.0.0.1:55432
uv sync                                                     # 엔진은 pyproject.toml에 고정한 버전을 GitHub에서 받는다
```

`taki.yml`(모델)과 `.env`(키)는 엔진 저장소 README대로 이 폴더에 둔다. 둘 다 커밋하지 않는다.

## 명령

```bash
uv run taki-server db-upgrade                           # 스키마 마이그레이션
uv run taki-server api [--port 8000] [--config taki.yml]  # 127.0.0.1에만 바인딩, 인증 없음
uv run taki-server worker [--once] [--config taki.yml]    # 대기 중인 검사를 돌린다. 결과 파일은 ./runs
uv run taki-server openapi > deploy/openapi.json        # API 명세 갱신
```

DB 주소는 `TAKI_DB_URL`로 바꾼다(기본값은 위 compose의 로컬 DB).

## 시험

```bash
uv run pytest              # DB 없이 도는 시험
uv run pytest -m postgres  # 위 compose의 PostgreSQL 필요. 시험마다 표를 비운다
```

## 엔진을 같이 고칠 때

```bash
uv pip install -e <엔진 체크아웃 경로>   # 고정 버전 대신 로컬 엔진을 잠시 쓴다
uv run --no-sync pytest                  # 덮어쓴 상태로 돌릴 때는 --no-sync
```

`--no-sync` 없는 `uv run`이나 `uv sync`는 잠금 파일의 고정 버전으로 되돌린다. 엔진 변경이 끝나면 엔진에 태그를 달고 `pyproject.toml`의 버전을 올린 뒤 `uv lock`한다.
