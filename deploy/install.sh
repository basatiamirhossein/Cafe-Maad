#!/usr/bin/env bash
# Installs or updates Cafe Maad on a server whose nginx already hosts other sites (e.g. datadevvv.ir).
# Run as root:  bash deploy/install.sh        (safe to run again for every update)
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/basatiamirhossein/Cafe-Maad.git}"
BRANCH="${BRANCH:-main}"
SRC_DIR="${SRC_DIR:-/opt/cafemaad}"
WEB_DIR="/var/www/cafemaad"
SITE_CONF="/etc/nginx/sites-available/cafemaad"

die() { echo "error: $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "run as root (sudo bash deploy/install.sh)"
command -v nginx >/dev/null || die "nginx is not installed"
command -v git >/dev/null || die "git is not installed (apt install git)"

fetch_source() {
    if [[ -d "$SRC_DIR/.git" ]]; then
        git -C "$SRC_DIR" fetch --depth 1 origin "$BRANCH"
        git -C "$SRC_DIR" reset --hard "origin/$BRANCH"
    else
        git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$SRC_DIR"
    fi
}

publish_page() {
    install -d -m 755 "$WEB_DIR"
    # Copy to a temp name first so visitors never get a half-written page.
    install -m 644 "$SRC_DIR/index.html" "$WEB_DIR/index.html.new"
    mv -f "$WEB_DIR/index.html.new" "$WEB_DIR/index.html"
}

install_nginx_site() {
    install -m 644 "$SRC_DIR/deploy/nginx-cafemaad.conf" "$SITE_CONF"
    ln -sfn "$SITE_CONF" /etc/nginx/sites-enabled/cafemaad
    nginx -t || die "nginx config test failed; other sites are untouched until it passes"
    systemctl reload nginx
}

fetch_source
publish_page
install_nginx_site

echo "ok: Cafe Maad published to $WEB_DIR"
echo "check: curl -sI -H 'Host: cafemaad.ir' http://127.0.0.1/ | head -n 1"
