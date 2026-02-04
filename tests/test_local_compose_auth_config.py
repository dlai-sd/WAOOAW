from __future__ import annotations

from pathlib import Path


def _extract_service_block(text: str, service_name: str) -> str:
    lines = text.splitlines()
    start = None
    header = f"  {service_name}:"
    for i, line in enumerate(lines):
        if line.rstrip() == header:
            start = i
            break

    if start is None:
        return ""

    out = [lines[start]]
    for line in lines[start + 1 :]:
        # Next service starts at same indentation (two spaces) and ends with ':'
        if line.startswith("  ") and not line.startswith("    ") and line.rstrip().endswith(":"):
            break
        out.append(line)
    return "\n".join(out)


def test_docker_compose_local_has_required_pp_to_plant_routing():
    compose_path = Path(__file__).resolve().parents[1] / "docker-compose.local.yml"
    text = compose_path.read_text(encoding="utf-8")
    block = _extract_service_block(text, "pp-backend")
    assert block, "pp-backend service missing"

    assert "PLANT_API_URL=http://plant-gateway:8000" in block
    assert "PLANT_API_URL=http://localhost" not in block


def test_docker_compose_local_has_gateway_auth_config_for_dev_tokens():
    compose_path = Path(__file__).resolve().parents[1] / "docker-compose.local.yml"
    text = compose_path.read_text(encoding="utf-8")
    block = _extract_service_block(text, "plant-gateway")
    assert block, "plant-gateway service missing"

    assert "JWT_ALGORITHM=HS256" in block
    assert "JWT_PUBLIC_KEY=${JWT_SECRET:-dev-secret-change-in-production}" in block
