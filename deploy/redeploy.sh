#!/usr/bin/env bash
# Rebuilds the frontend and pushes backend + frontend changes to the live Azure VM.
# Run from the repo root (Git Bash / WSL) after committing your changes locally.
set -euo pipefail

VM_HOST="azureuser@20.219.167.97"
SSH_KEY="$HOME/.ssh/meetiq_azure"
TMP_DIR="$(mktemp -d)"

echo "==> Building frontend"
(cd frontend && VITE_API_BASE_URL="" npm run build)

echo "==> Packaging backend"
tar -czf "$TMP_DIR/backend.tar.gz" \
  --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.pytest_cache' --exclude='uploads' --exclude='*.db' --exclude='.env' \
  -C backend app requirements.txt

echo "==> Packaging frontend"
tar -czf "$TMP_DIR/frontend.tar.gz" -C frontend/dist .

echo "==> Uploading"
scp -i "$SSH_KEY" "$TMP_DIR/backend.tar.gz" "$VM_HOST:/opt/meetiq/backend/"
scp -i "$SSH_KEY" "$TMP_DIR/frontend.tar.gz" "$VM_HOST:/var/www/meetiq/"

echo "==> Deploying on server"
ssh -i "$SSH_KEY" "$VM_HOST" bash -s <<'EOF'
set -e
cd /opt/meetiq/backend
tar -xzf backend.tar.gz && rm backend.tar.gz
.venv/bin/pip install -r requirements.txt -q
sudo systemctl restart meetiq-backend

cd /var/www/meetiq
find . -mindepth 1 -not -name 'frontend.tar.gz' -delete 2>/dev/null || true
tar -xzf frontend.tar.gz && rm frontend.tar.gz

for i in 1 2 3 4 5; do
  sleep 1
  sudo systemctl is-active meetiq-backend && curl -sf http://127.0.0.1:8000/api/health && break
  [ "$i" -eq 5 ] && { echo "backend did not come up healthy" >&2; exit 1; }
done
EOF

rm -rf "$TMP_DIR"
echo "==> Done: https://unthink-meetiq.centralindia.cloudapp.azure.com"
