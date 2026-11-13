<div align="center">
  <img src="./assets/taki-logo.svg" alt="TAKI 로고" width="140" />
  <h1>TAKI 서버</h1>
  <p>진단 요청 · 검사 실행 · 결과 조회</p>
</div>

TAKI는 [진단 엔진](https://github.com/what-is-your-vulnerability/security-diagnosis-agent)의 CLI로 직접 실행할 수 있다. 이 서버는 검사 대기열과 로컬 HTTP API가 필요할 때 사용한다. API가 요청을 대기열에 넣으면 별도 worker가 엔진을 실행해 결과를 PostgreSQL에 저장한다.

## 실행

Python 3.12, `uv`, Docker가 필요하다. 엔진 설정 예시에 따라 `taki.yml`을 만들고 모델·API 키를 설정한다. 키와 설정 파일은 커밋하지 않는다.

```bash
docker compose -f deploy/docker-compose.yml up -d --wait
uv sync
uv run taki-server db-upgrade
```

API와 worker를 각각 다른 터미널에서 실행한다.

```bash
uv run taki-server api --config taki.yml
uv run taki-server worker --config taki.yml
```

API 문서는 `http://127.0.0.1:8000/docs`에서 볼 수 있다. 프로젝트를 등록(`POST /api/v1/projects`)하고 검사를 요청(`POST /api/v1/scans`)한 뒤, `GET /api/v1/scans/{id}`와 `GET /api/v1/scans/{id}/report`에서 상태와 결과를 확인한다. 설계문서 등록·규칙 도출·승인 API도 제공한다.

API에는 인증이 없고 `127.0.0.1`에만 바인딩한다. DB 기본 주소는 위 Compose의 로컬 PostgreSQL이며, `TAKI_DB_URL`로 바꿀 수 있다. 엔진은 `pyproject.toml`에 지정된 태그 버전을 설치한다.

## 검증

```bash
uv run pytest
uv run pytest -m postgres
```

두 번째 명령은 위 PostgreSQL이 실행 중이어야 한다.
