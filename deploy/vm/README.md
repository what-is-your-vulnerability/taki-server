# VM 1대에 배포하기

API와 worker는 VM의 systemd 서비스로, PostgreSQL은 이 VM의 Docker 컨테이너로 돌린다.
worker가 엔진을 통해 `docker run`으로 스캐너를 띄우고 호스트 경로를 그대로 마운트하기 때문에 API·worker를 컨테이너에 넣지 않는다.

> 이 절차의 로컬 부분(`uv sync`, 마이그레이션, 시험, compose, 백업 덤프)은 개발 PC에서 확인했다.
> systemd 서비스 기동은 아직 실제 VM에서 확인하지 않았다.

## 준비

- Ubuntu 22.04 이상, Docker와 Docker Compose, `uv`(Python 3.12는 uv가 받는다)
- 아웃바운드 HTTPS: `api.openai.com`(모델 호출), `github.com`(엔진 의존성 설치), PyPI, 스캐너 이미지를 받는 레지스트리.
  `api.openai.com`이 막혀 있으면 규칙 도출과 검사가 동작하지 않는다.
- 인바운드: 외부에 열지 않는다. API는 `127.0.0.1:8000`에만 열리고 인증이 없다. 접속은 SSH 터널로 한다.

## 설치

```bash
sudo useradd --system --create-home --home-dir /var/lib/taki-server --shell /usr/sbin/nologin taki
sudo usermod -aG docker taki            # worker가 스캐너를 띄운다. docker 그룹은 root 권한과 같다.
sudo git clone https://github.com/what-is-your-vulnerability/taki-server /opt/taki-server
sudo chown -R taki:taki /opt/taki-server && cd /opt/taki-server
sudo -u taki uv sync --frozen           # 엔진(taki)은 잠금 파일에 고정한 버전을 GitHub에서 받는다
```

## 설정 (비밀값은 저장소에 두지 않는다)

```bash
sudo install -d -m 750 -o root -g taki /etc/taki
# 비밀번호는 직접 만든다. 아래의 <...>를 채운다.
sudo tee /etc/taki/taki.env >/dev/null <<'ENV'
TAKI_DB_PASSWORD=<DB 비밀번호>
TAKI_DB_URL=postgresql+psycopg://taki:<DB 비밀번호>@127.0.0.1:55432/taki
OPENAI_API_KEY=<키>
# LangSmith는 쓰지 않는다. TAKI_LANGSMITH_PROJECT를 적지 않는다.
ENV
sudo chown root:taki /etc/taki/taki.env && sudo chmod 640 /etc/taki/taki.env
# 모델 설정은 엔진 저장소의 예제를 복사해 역할별 모델을 적는다. 커밋하지 않는다.
sudo -u taki curl -fsSL -o /var/lib/taki-server/taki.yml \
  https://raw.githubusercontent.com/what-is-your-vulnerability/Threat-Analysis-Knowledge-Intelligence/v0.2.0/taki.example.yml
```

`TAKI_DB_URL`은 `.env`가 아니라 프로세스 환경변수로만 읽힌다. 그래서 systemd의 `EnvironmentFile`로 넘긴다.

## 기동

```bash
cd /opt/taki-server
set -a; . /etc/taki/taki.env; set +a
docker compose -f deploy/vm/docker-compose.yml up -d --wait
sudo -E -u taki .venv/bin/taki-server db-upgrade
sudo cp deploy/vm/taki-api.service deploy/vm/taki-worker.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now taki-api taki-worker
```

## 확인

```bash
systemctl status taki-api taki-worker --no-pager
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/docs      # 200
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: x.example' http://127.0.0.1:8000/docs   # 400
journalctl -u taki-worker -n 50 --no-pager
```

내 PC에서 API를 보려면 `ssh -L 8000:127.0.0.1:8000 <VM>` 후 `http://127.0.0.1:8000/docs`.

## 백업과 삭제

```bash
sudo -u taki /opt/taki-server/deploy/vm/backup.sh /var/backups/taki
```

DB 덤프와 `runs/`를 함께 백업한다. 보관 기간이 지난 백업과 `runs/scan-*`, `runs/derive-*`는 직접 지운다.
현재 코드에는 삭제 API와 자동 정리가 없다. 기준은 WBS 2.5 문서를 따른다.

## 엔진 버전 올리기

엔진 저장소에서 태그를 달고 `pyproject.toml`의 버전을 올린 뒤 `uv lock`한 커밋을 받아, VM에서 `sudo -u taki uv sync --frozen`과 `sudo systemctl restart taki-api taki-worker`를 한다.

## 알려진 한계

- worker가 죽으면 실행 중이던 검사는 `running`으로 남는다. 서비스는 재시작되지만 그 검사는 복구되지 않는다.
- API에 인증이 없다. 외부에 열지 않는다.
