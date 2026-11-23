#!/bin/sh
# MedShare-Lab — Vault lab bootstrap (persistent file storage + auto-unseal).
#
# First start : init (1 key share), unseal, create the fixed lab root token
#               VAULT_LAB_ROOT_TOKEN, enable the Transit engine.
# Every start : unseal with the stored key, re-check token and Transit (idempotent).
#
# LAB ONLY: the unseal key and initial root token are stored in
# infra/runtime/vault/.lab-init (gitignored) next to the encrypted data, so the
# seal offers no protection against someone holding the volume. Production must
# use a real auto-unseal (HSM / cloud KMS) or Shamir shares held by people.

export VAULT_ADDR="http://127.0.0.1:8200"
INIT_FILE="/vault/file/.lab-init"
LAB_TOKEN="${VAULT_LAB_ROOT_TOKEN:-dev-root-token-topic18}"

vault server -config=/vault/config/config.hcl &
VAULT_PID=$!
trap 'kill -TERM "$VAULT_PID" 2>/dev/null; wait "$VAULT_PID"; exit 0' TERM INT

# Wait until the listener answers (vault status: 0=unsealed, 2=sealed, 1=error).
while :; do
  vault status >/dev/null 2>&1
  [ $? -ne 1 ] && break
  kill -0 "$VAULT_PID" 2>/dev/null || { echo "[vault-lab] server exited"; exit 1; }
  sleep 1
done

vault operator init -status >/dev/null 2>&1
if [ $? -eq 2 ]; then
  echo "[vault-lab] Initialising new Vault (1 key share)..."
  umask 077
  vault operator init -key-shares=1 -key-threshold=1 > "$INIT_FILE" || exit 1
fi

UNSEAL_KEY=$(awk '/Unseal Key 1:/ {print $4}' "$INIT_FILE")
INIT_ROOT=$(awk '/Initial Root Token:/ {print $4}' "$INIT_FILE")
if [ -z "$UNSEAL_KEY" ] || [ -z "$INIT_ROOT" ]; then
  echo "[vault-lab] Cannot read $INIT_FILE"; exit 1
fi

vault status >/dev/null 2>&1
if [ $? -eq 2 ]; then
  vault operator unseal "$UNSEAL_KEY" >/dev/null || exit 1
  echo "[vault-lab] Unsealed."
fi

if ! VAULT_TOKEN="$INIT_ROOT" vault token lookup "$LAB_TOKEN" >/dev/null 2>&1; then
  VAULT_TOKEN="$INIT_ROOT" vault token create -id="$LAB_TOKEN" -policy=root -orphan >/dev/null || exit 1
  echo "[vault-lab] Created lab root token."
fi

if ! VAULT_TOKEN="$LAB_TOKEN" vault secrets list | grep -q '^transit/'; then
  VAULT_TOKEN="$LAB_TOKEN" vault secrets enable transit >/dev/null || exit 1
  echo "[vault-lab] Enabled Transit secrets engine."
fi

echo "[vault-lab] Ready (persistent storage: /vault/file)."
wait "$VAULT_PID"
