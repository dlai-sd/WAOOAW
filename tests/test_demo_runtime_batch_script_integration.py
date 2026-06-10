import os
import subprocess
from pathlib import Path


SCRIPT = Path("scripts/demo-runtime-batch.sh")


def _run(action: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "DRY_RUN": "true",
            "TARGET_ENVIRONMENT": "demo",
            "GCP_PROJECT_ID": "waooaw-oauth",
            "GCP_REGION": "asia-south1",
            "START_MIN_GATEWAY": "1",
        }
    )
    return subprocess.run(
        ["bash", str(SCRIPT), action],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_stop_outputs_all_expected_demo_services() -> None:
    result = _run("stop")
    assert result.returncode == 0, result.stderr

    output = result.stdout
    assert "waooaw-cp-frontend-demo" in output
    assert "waooaw-cp-backend-demo" in output
    assert "waooaw-pp-frontend-demo" in output
    assert "waooaw-pp-backend-demo" in output
    assert "waooaw-plant-gateway-demo" in output

    # Stop action should force min instances to zero for all scoped services.
    assert output.count("--min-instances 0") >= 5


def test_start_uses_gateway_min_instance_override() -> None:
    result = _run("start")
    assert result.returncode == 0, result.stderr

    output = result.stdout
    assert "waooaw-plant-gateway-demo" in output
    assert "--min-instances 1" in output


def test_rejects_non_demo_environment() -> None:
    env = os.environ.copy()
    env.update(
        {
            "DRY_RUN": "true",
            "TARGET_ENVIRONMENT": "uat",
        }
    )

    result = subprocess.run(
        ["bash", str(SCRIPT), "stop"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 3
    assert "Refusing to run outside demo" in result.stderr
