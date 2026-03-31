from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


REPO_ROOT = Path("/workspaces/WAOOAW")
SCRIPT_PATH = REPO_ROOT / "cloud/scripts/provision-managed-redis.sh"


def _make_fake_gcloud(tmp_path: Path) -> Path:
    log_path = tmp_path / "gcloud.log"
    fake_path = tmp_path / "gcloud"
    fake_path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_GCLOUD_LOG:?}"

if [[ "$1 $2 $3" == "redis instances describe" ]]; then
  printf '10.9.0.7\n'
  exit 0
fi

if [[ "$1 $2 $3" == "redis instances create" ]]; then
  exit 0
fi

if [[ "$1 $2" == "secrets describe" ]]; then
  exit 1
fi

if [[ "$1 $2" == "secrets create" ]]; then
  exit 0
fi

if [[ "$1 $2 $3" == "secrets versions add" ]]; then
  cat >/dev/null
  exit 0
fi

printf 'unexpected gcloud args: %s\n' "$*" >&2
exit 1
""",
        encoding="utf-8",
    )
    fake_path.chmod(fake_path.stat().st_mode | stat.S_IEXEC)
    return log_path


def test_provision_managed_redis_help() -> None:
    completed = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "--project <id>" in completed.stdout
    assert "--region <region>" in completed.stdout
    assert "--environment <env>" in completed.stdout
    assert "--network <network>" in completed.stdout
    assert "--dry-run" in completed.stdout


def test_provision_managed_redis_dry_run() -> None:
    completed = subprocess.run(
        [
            "bash",
            str(SCRIPT_PATH),
            "--project",
            "waooaw-oauth",
            "--region",
            "asia-south1",
            "--environment",
            "demo",
            "--network",
            "projects/waooaw-oauth/global/networks/default",
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert (
      "Planned create:" in completed.stderr
      or "already exists in asia-south1 with host" in completed.stderr
    )
    assert "demo-plant-backend-redis-url" in completed.stderr
    assert (
      "redis://DRY_RUN_REDIS_HOST_demo:6379/0" in completed.stderr
      or "redis://10.53.167.11:6379/0" in completed.stderr
    )
    assert (
      "redis://DRY_RUN_REDIS_HOST_demo:6379/3" in completed.stderr
      or "redis://10.53.167.11:6379/3" in completed.stderr
    )


def test_provision_managed_redis_apply_with_fake_gcloud(tmp_path: Path) -> None:
    log_path = _make_fake_gcloud(tmp_path)
    env = os.environ.copy()
    env["FAKE_GCLOUD_LOG"] = str(log_path)
    env["GCLOUD_BIN"] = str(tmp_path / "gcloud")

    subprocess.run(
        [
            "bash",
            str(SCRIPT_PATH),
            "--project",
            "waooaw-oauth",
            "--region",
            "asia-south1",
            "--environment",
            "demo",
            "--network",
            "projects/waooaw-oauth/global/networks/default",
            "--apply",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    log_text = log_path.read_text(encoding="utf-8")
    assert "redis instances describe waooaw-redis-demo --region asia-south1 --project waooaw-oauth --format=value(host)" in log_text
    assert "secrets create demo-plant-backend-redis-url --project waooaw-oauth --replication-policy automatic" in log_text
    assert "secrets versions add demo-plant-backend-redis-url --project waooaw-oauth --data-file=-" in log_text
    assert "secrets versions add demo-plant-gateway-redis-url --project waooaw-oauth --data-file=-" in log_text
    assert "secrets versions add demo-pp-backend-redis-url --project waooaw-oauth --data-file=-" in log_text
    assert "secrets versions add demo-cp-backend-redis-url --project waooaw-oauth --data-file=-" in log_text