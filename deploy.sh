#!/usr/bin/env bash
# Build index.html from prototype.html and deploy.
#   ./deploy.sh           → build + deploy frontend (index.html)
#   ./deploy.sh back      → deploy backend (app.py) + restart service
#   ./deploy.sh all       → frontend + backend
#   ./deploy.sh build     → build index.html only (no deploy)
set -euo pipefail
cd "$(dirname "$0")"
KEY=~/.ssh/id_rsa_smart_shelf
HOST=root@212.24.97.97
WEB=/var/www/fungeneering.com/notes/index.html
APP=/opt/dotline/app.py

build() {
  cat > /tmp/_dl_head.html <<'EOF'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-color" content="#128074" />
<title>Dotline — linear notes</title>
<script src="https://accounts.google.com/gsi/client" async></script>
<style>
  html, body { margin: 0; padding: 0; }
  *, *::before, *::after { box-sizing: border-box; }
</style>
</head>
<body>
EOF
  printf '</body>\n</html>\n' > /tmp/_dl_tail.html
  cat /tmp/_dl_head.html prototype.html /tmp/_dl_tail.html > index.html
  rm -f /tmp/_dl_head.html /tmp/_dl_tail.html
  echo "built index.html ($(wc -c < index.html) bytes)"
}

put_front() { scp -i "$KEY" -o BatchMode=yes index.html "$HOST:$WEB"; }
put_back()  { scp -i "$KEY" -o BatchMode=yes backend/app.py "$HOST:$APP"; \
              ssh -i "$KEY" -o BatchMode=yes "$HOST" 'systemctl restart dotline-api'; }

build
case "${1:-front}" in
  front) put_front ;;
  back)  put_back ;;
  all)   put_front; put_back ;;
  build) ;;
  *) echo "unknown target: $1" >&2; exit 1 ;;
esac
[ "${1:-front}" != build ] && curl -s -o /dev/null -w "live: %{http_code}\n" https://fungeneering.com/notes/ || true
