from pathlib import Path


def test_workflow_declares_stop_start_actions() -> None:
    workflow = Path(".github/workflows/waooaw-demo-runtime-batch.yml").read_text(encoding="utf-8")

    assert "name: WAOOAW Demo Runtime Batch" in workflow
    assert "options: [stop, start]" in workflow
    assert "TARGET_ENVIRONMENT: demo" in workflow


def test_workflow_has_no_terraform_steps() -> None:
    workflow = Path(".github/workflows/waooaw-demo-runtime-batch.yml").read_text(encoding="utf-8").lower()

    assert "terraform " not in workflow
    assert "terraform_apply" not in workflow
    assert "terraform_plan" not in workflow


def test_workflow_requires_confirmation_tokens() -> None:
    workflow = Path(".github/workflows/waooaw-demo-runtime-batch.yml").read_text(encoding="utf-8")

    assert "STOP_DEMO_RUNTIME" in workflow
    assert "START_DEMO_RUNTIME" in workflow
