#!/usr/bin/env python3
"""
Generate environment tfvars from infrastructure.yaml so Terraform is driven by the
single YAML source of truth.

Usage:
  python generate_tfvars.py --env demo
  python generate_tfvars.py --env demo --env uat --env prod

Outputs:
  Writes environments/<env>.tfvars with image tags, project, region, domains, etc.

Note: Requires PyYAML (`pip install pyyaml`) if not already available.
"""

import argparse
import pathlib
from typing import Dict, Any

import yaml

ROOT = pathlib.Path(__file__).resolve().parent
INFRA_FILE = ROOT.parent / "infrastructure.yaml"
ENV_DIR = ROOT / "environments"

SHARED_STATIC_IP_NAME = "waooaw-lb-ip"  # Shared IP across envs


def load_config() -> Dict[str, Any]:
    with INFRA_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def compute_domains(env: str, domain: str) -> Dict[str, str]:
    if env == "prod":
        return {
            "customer_portal": f"www.{domain}",
            "platform_portal": f"pp.{domain}",
        }
    return {
        "customer_portal": f"cp.{env}.{domain}",
        "platform_portal": f"pp.{env}.{domain}",
    }


def compute_images(cfg: Dict[str, Any], env: str) -> Dict[str, str]:
    project = cfg["config"]["project"]
    registry = cfg["images"].get("registry", "asia-south1-docker.pkg.dev")
    version = cfg.get("properties", {}).get("version", "latest")

    backend_repo = f"{project}/waooaw/backend-v2"
    platform_repo = f"{project}/waooaw/platform-portal-v2"
    customer_repo = f"{project}/waooaw/customer-portal-v2"

    return {
        "backend_image": f"{registry}/{backend_repo}:{version}",
        "platform_portal_image": f"{registry}/{platform_repo}:{version}",
        # Customer portal image kept in case we enable it; use same versioning.
        "customer_portal_image": f"{registry}/{customer_repo}:{version}",
    }


def write_tfvars(env: str, cfg: Dict[str, Any]) -> None:
    domain = cfg["config"]["domain"]
    project = cfg["config"]["project"]
    region = cfg["config"].get("region_primary", "asia-south1")
    scaling = cfg["scaling"][env]
    domains = compute_domains(env, domain)
    images = compute_images(cfg, env)

    lines = [
        f'environment              = "{env}"',
        f'project_id               = "{project}"',
        f'region                   = "{region}"',
        f'static_ip_name           = "{SHARED_STATIC_IP_NAME}"',
        f'backend_image            = "{images["backend_image"]}"',
        f'customer_portal_image    = "{images["customer_portal_image"]}"',
        f'platform_portal_image    = "{images["platform_portal_image"]}"',
        'domains = {',
        f'  {env} = {{',
        f'    customer_portal = "{domains["customer_portal"]}",',
        f'    platform_portal = "{domains["platform_portal"]}",',
        '  }',
        '}',
        'scaling = {',
        f'  {env} = {{ min = {scaling["min_instances"]}, max = {scaling["max_instances"]} }}',
        '}',
    ]

    ENV_DIR.mkdir(parents=True, exist_ok=True)
    out_file = ENV_DIR / f"{env}.tfvars"
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ wrote {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate tfvars from infrastructure.yaml")
    parser.add_argument("--env", dest="envs", action="append", required=True, help="Environment(s) to generate: demo, uat, prod")
    args = parser.parse_args()

    cfg = load_config()

    for env in args.envs:
        if env not in ("demo", "uat", "prod"):
            raise SystemExit(f"Unsupported environment: {env}")
        write_tfvars(env, cfg)


if __name__ == "__main__":
    main()
