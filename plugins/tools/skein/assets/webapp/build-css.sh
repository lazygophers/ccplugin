#!/usr/bin/env bash
# Rebuild dist/app.css after editing tailwind classes / src/input.css.
# ponytail: tailwind binary lives in ~/.cache/skein (46MB), never committed.
set -euo pipefail

VER=v3.4.17
case "$(uname -s)" in Darwin) OS=macos ;; Linux) OS=linux ;; *) echo "unsupported OS"; exit 1 ;; esac
case "$(uname -m)" in arm64|aarch64) ARCH=arm64 ;; x86_64|amd64) ARCH=x64 ;; *) echo "unsupported arch"; exit 1 ;; esac

BIN="${TAILWIND_BIN:-$HOME/.cache/skein/tailwindcss-$OS-$ARCH}"
if [ ! -x "$BIN" ]; then
  mkdir -p "$(dirname "$BIN")"
  echo "downloading tailwind $VER -> $BIN"
  curl -fL "https://github.com/tailwindlabs/tailwindcss/releases/download/$VER/tailwindcss-$OS-$ARCH" -o "$BIN"
  chmod +x "$BIN"
fi

cd "$(dirname "$0")"
"$BIN" -i src/input.css -o dist/app.css --minify -c tailwind.config.js
