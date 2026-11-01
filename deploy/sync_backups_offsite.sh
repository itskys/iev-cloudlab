#!/bin/bash
# IEV CloudLab 备份异地同步：Hostinger → DMIT 备用机
# 每日 03:05 cron 执行（02:30 本地备份之后）；镜像备份目录，不含临时文件
# 保护：源端少于 3 份备份时拒绝同步（防止源端异常导致异地被清空）
set -u
SRC="/opt/ievlab/backups/"
DST="root@69.63.206.190:/opt/ievlab-backups/"
KEY="/root/.ssh/id_ievlab_offsite"
LOG="/opt/ievlab/deploy/offsite_sync.log"
N=$(ls "$SRC"ievlab_backup_*.tar.gz 2>/dev/null | wc -l)
if [ "$N" -lt 3 ]; then
  echo "$(date '+%F %T') ABORT: only $N local backups, refusing to mirror" >> "$LOG"
  exit 1
fi
rsync -az --delete --exclude='.tmp_*' -e "ssh -i $KEY -o BatchMode=yes -o ConnectTimeout=30" "$SRC" "$DST" >> "$LOG" 2>&1
RC=$?
echo "$(date '+%F %T') offsite sync exit=$RC (mirrored $N backups)" >> "$LOG"
exit $RC
