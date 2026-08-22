#!/usr/bin/env bash
set -e

echo "Yangi kodlar yuklab olinmoqda..."
 git pull

echo "Server yangilanmoqda (docker)..."
 docker compose up -d --build

echo "Muvaffaqiyatli tugatildi!"
