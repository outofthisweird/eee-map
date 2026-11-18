#!/bin/sh
# nycta-gsm 디자인 시스템의 공개 결과물(web/ 안의 CSS·배포 서체·노선도 계산 스크립트)만 vendor/nycta/로 복사한다.
# 원장·데이터 같은 비공개 원본은 절대 가져오지 않는다. 헬베티카 미리보기(web/preview/)도 제외.
# 기본은 형제 폴더 nycta-gsm(공개 publish 결과, 루트에 css/·js/·fonts/)이다. 먼저 git pull로 최신 publish를 받는다.
# 없으면 nycta-gsm-src의 web/를 쓴다. NYCTA_DIR=경로 로 직접 지정해도 된다(루트나 web/ 둘 다 됨).
set -e
cd "$(dirname "$0")/.."
for d in ${NYCTA_DIR:-../nycta-gsm ../nycta-gsm-src}; do
  if [ -f "$d/css/nycta.css" ]; then NYCTA_DIR="$d"; W="$d"; break; fi
  if [ -f "$d/web/css/nycta.css" ]; then NYCTA_DIR="$d"; W="$d/web"; break; fi
done
[ -n "$W" ] || { echo "nycta-gsm 결과물을 찾지 못함. NYCTA_DIR=경로 로 지정하세요." >&2; exit 1; }
mkdir -p vendor/nycta
cp "$W/css/nycta.css" vendor/nycta/nycta.css
cp "$W/fonts/albert-sans-nycta-wght.woff2" "$W/fonts/OFL-AlbertSans.txt" vendor/nycta/
cp "$W/fonts/nycta-hangul.woff2" "$W/fonts/OFL-SUIT.txt" vendor/nycta/   # DEC-032 한글(SUIT 파생, OFL)
cp "$W/js/nycta-map.js" vendor/nycta/nycta-map.js   # DEC-036 노선도: NYCTAMap.geometry(꺾임·선 길이·이름 자리 계산)
{ echo "source: github.com/outofthisweird/nycta-gsm (public web/ output)"
  echo "commit: $(git -C "$NYCTA_DIR" log -1 --format='%h %cs %s' 2>/dev/null || echo unknown)"; } > vendor/nycta/SOURCE.txt
echo "vendor/nycta 갱신됨 ($NYCTA_DIR) — python3 build.py 로 index.html 다시 만들기"
