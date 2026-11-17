#!/bin/sh
# 로컬 헬베티카 미리보기 서체를 nycta-gsm 원본 저장소에서 만들어 ./preview/ 로 복사한다.
# preview/ 는 git 제외 — 절대 커밋하거나 배포하지 않는다(nycta-gsm DEC-028).
# nycta 폴더는 NYCTA_DIR 로 지정하거나, 형제 폴더 nycta-gsm-src / nycta-gsm 중 Makefile 있는 쪽을 쓴다.
set -e
cd "$(dirname "$0")/.."
if [ -z "$NYCTA_DIR" ]; then
  for d in ../nycta-gsm-src ../nycta-gsm; do
    [ -f "$d/Makefile" ] && [ -f "$d/tools/build_fonts.py" ] && NYCTA_DIR="$d" && break
  done
fi
[ -n "$NYCTA_DIR" ] || { echo "nycta-gsm 원본 저장소를 찾지 못함. NYCTA_DIR=경로 로 지정하세요." >&2; exit 1; }
[ -x "$NYCTA_DIR/.venv/bin/python" ] || make -C "$NYCTA_DIR" setup
make -C "$NYCTA_DIR" preview
rm -rf preview && cp -R "$NYCTA_DIR/web/preview" preview
echo "preview/ 준비됨 ($NYCTA_DIR)"
