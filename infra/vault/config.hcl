# MedShare-Lab — Vault KMS (Zone Z1), persistent lab configuration.
# Replaces `vault server -dev` (in-memory) so Transit KEKs survive container restarts.
storage "file" {
  path = "/vault/file"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1 # Lab only. Internal mTLS is tracked in plan-mTLS.md / TIEN_DO_HIEN_TAI.md §7.
}

api_addr          = "http://127.0.0.1:8200"
ui                = true
disable_mlock     = true
default_lease_ttl = "87600h"
max_lease_ttl     = "87600h"
