#!/usr/bin/env bash
# DB 덤프와 runs/를 묶어 보관한다. 사용: sudo -u taki deploy/vm/backup.sh /path/to/backup-dir
# 보관 기간이 지난 백업은 따로 지워야 한다(자료 보관·삭제 기준 문서 참고).
set -euo pipefail
dest="${1:?백업 폴더를 인자로 주세요}"
stamp="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$dest"
umask 077
docker exec taki-postgres-1 pg_dump -U taki -d taki -Fc > "$dest/taki-db-$stamp.dump"
tar -czf "$dest/taki-runs-$stamp.tar.gz" -C /var/lib/taki-server runs
echo "백업 완료: $dest ($stamp)"
