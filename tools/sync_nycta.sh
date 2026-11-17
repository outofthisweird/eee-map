#!/bin/sh
# nycta-gsm 디자인 시스템의 공개 결과물(web/ 안의 CSS·배포 서체)만 vendor/nycta/로 복사한다.
# 원장·데이터 같은 비공개 원본은 절대 가져오지 않는다. 헬베티카 미리보기(web/preview/)도 제외.
# nycta 폴더는 NYCTA_DIR 로 지정하거나, 형제 폴더 nycta-gsm-src / nycta-gsm 중 web/css/nycta.css 있는 쪽을 쓴다.
set -e
cd "$(dirname "$0")/.."
if [ -z "$NYCTA_DIR" ]; then
  for d in ../nycta-gsm-src ../nycta-gsm; do
    [ -f "$d/web/css/nycta.css" ] && NYCTA_DIR="$d" && break
  done
fi
[ -n "$NYCTA_DIR" ] || { echo "nycta-gsm 저장소를 찾지 못함. NYCTA_DIR=경로 로 지정하세요." >&2; exit 1; }
W="$NYCTA_DIR/web"
mkdir -p vendor/nycta
cp "$W/css/nycta.css" vendor/nycta/nycta.css
cp "$W/fonts/albert-sans-nycta-wght.woff2" "$W/fonts/OFL-AlbertSans.txt" vendor/nycta/
cp "$W/fonts/nycta-hangul.woff2" "$W/fonts/OFL-SUIT.txt" vendor/nycta/   # DEC-032 한글(SUIT 파생, OFL)
{ echo "source: github.com/outofthisweird/nycta-gsm (public web/ output)"
  echo "commit: $(git -C "$NYCTA_DIR" log -1 --format='%h %cs %s' 2>/dev/null || echo unknown)"; } > vendor/nycta/SOURCE.txt
echo "vendor/nycta 갱신됨 ($NYCTA_DIR) — python3 build.py 로 index.html 다시 만들기"
