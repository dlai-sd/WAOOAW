import tempfile
from pathlib import Path

from agent_mold.skills.executor import execute_marketing_multichannel_v1
from agent_mold.skills.loader import PlaybookLoadError, load_playbook, load_playbook_with_certification
from agent_mold.skills.adapters import adapt_facebook, adapt_instagram, adapt_linkedin, adapt_whatsapp, adapt_youtube
from agent_mold.skills.playbook import ChannelName, SkillExecutionInput


def test_load_marketing_playbook_and_execute_variants():
    backend_root = Path(__file__).resolve().parents[2]
    playbook_path = backend_root / "agent_mold" / "playbooks" / "marketing" / "multichannel_post_v1.md"

    playbook = load_playbook(playbook_path)
    assert playbook.metadata.playbook_id == "MARKETING.MULTICHANNEL.POST.V1"
    assert playbook.metadata.output_contract == "marketing_multichannel_v1"

    result = execute_marketing_multichannel_v1(
        playbook,
        SkillExecutionInput(
            theme="5 quick tips for healthier skin",
            brand_name="Glow Beauty Studio",
            offer="Free consultation this week",
            location="Pune",
            audience="Working professionals",
            tone="Friendly and expert",
            language="Marathi + English blend",
        ),
    )

    assert result.output.canonical.theme
    channels = {v.channel for v in result.output.variants}
    assert ChannelName.YOUTUBE in channels
    assert ChannelName.FACEBOOK in channels
    assert ChannelName.LINKEDIN in channels
    assert ChannelName.INSTAGRAM in channels
    assert ChannelName.WHATSAPP in channels

    youtube = next(v for v in result.output.variants if v.channel == ChannelName.YOUTUBE)
    facebook = next(v for v in result.output.variants if v.channel == ChannelName.FACEBOOK)
    linkedin = next(v for v in result.output.variants if v.channel == ChannelName.LINKEDIN)
    insta = next(v for v in result.output.variants if v.channel == ChannelName.INSTAGRAM)
    whatsapp = next(v for v in result.output.variants if v.channel == ChannelName.WHATSAPP)

    assert len(youtube.text) <= 5100
    assert len(facebook.text) <= 63206
    assert len(linkedin.text) <= 3000
    assert len(insta.text) <= 2200
    assert len(whatsapp.text) <= 1024
    assert "#WAOOAW" in linkedin.text or "#WAOOAW" in " ".join(linkedin.hashtags)


def test_executor_respects_explicit_channel_list_order_and_dedupes():
    backend_root = Path(__file__).resolve().parents[2]
    playbook_path = backend_root / "agent_mold" / "playbooks" / "marketing" / "multichannel_post_v1.md"
    playbook = load_playbook(playbook_path)

    result = execute_marketing_multichannel_v1(
        playbook,
        SkillExecutionInput(
            theme="Clinic special announcement",
            brand_name="Care Clinic",
            channels=[ChannelName.WHATSAPP, ChannelName.LINKEDIN, ChannelName.WHATSAPP],
        ),
    )

    assert [v.channel for v in result.output.variants] == [ChannelName.WHATSAPP, ChannelName.LINKEDIN]


def test_loader_returns_certification_status_for_valid_playbook():
    backend_root = Path(__file__).resolve().parents[2]
    playbook_path = backend_root / "agent_mold" / "playbooks" / "marketing" / "multichannel_post_v1.md"

    playbook, cert = load_playbook_with_certification(playbook_path)
    assert playbook.metadata.playbook_id
    assert cert.certifiable is True
    assert cert.issues == []


def test_missing_quality_checks_is_not_certifiable_but_schema_valid():
    markdown = """---
playbook_id: MARKETING.TEST.NOQA.V1
name: Test
version: 1.0.0
category: marketing
description: test
output_contract: marketing_multichannel_v1
required_inputs: [theme, brand_name]
steps:
  - Draft
---
Body\n"""

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pb.md"
        path.write_text(markdown, encoding="utf-8")

        _playbook, cert = load_playbook_with_certification(path)
        assert cert.certifiable is False
        assert any("quality_checks" in issue for issue in cert.issues)


def test_schema_tightening_rejects_empty_steps_and_bad_semver():
    markdown = """---
playbook_id: MARKETING.TEST.BAD.V1
name: Test
version: 1
category: marketing
description: test
output_contract: marketing_multichannel_v1
required_inputs: [theme, brand_name]
steps: []
quality_checks: [No false claims]
---
Body\n"""

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pb.md"
        path.write_text(markdown, encoding="utf-8")

        try:
            load_playbook(path)
            assert False, "Expected PlaybookLoadError"
        except PlaybookLoadError as exc:
            message = str(exc)
            assert "schema validation" in message
            assert "metadata.version" in message or "version" in message


def test_adapters_preserve_required_canonical_fields():
    backend_root = Path(__file__).resolve().parents[2]
    playbook_path = backend_root / "agent_mold" / "playbooks" / "marketing" / "multichannel_post_v1.md"
    playbook = load_playbook(playbook_path)

    result = execute_marketing_multichannel_v1(
        playbook,
        SkillExecutionInput(
            theme="Grand opening",
            brand_name="Cake Shop",
            offer="20% off",
            location="Mumbai",
            audience="Families",
            tone="Warm",
            language="English",
        ),
    )

    canonical = result.output.canonical
    assert canonical.schema_version == "1.0"
    assert canonical.core_message
    assert canonical.call_to_action

    variants = [
        adapt_linkedin(canonical),
        adapt_instagram(canonical),
        adapt_youtube(canonical),
        adapt_facebook(canonical),
        adapt_whatsapp(canonical),
    ]

    assert {v.channel for v in variants} == {
        ChannelName.LINKEDIN,
        ChannelName.INSTAGRAM,
        ChannelName.YOUTUBE,
        ChannelName.FACEBOOK,
        ChannelName.WHATSAPP,
    }

    for v in variants:
        assert v.text
        assert canonical.core_message.split(":")[0] in v.text  # brand prefix survives
        assert v.hashtags


def test_trading_playbook_loads_and_is_certifiable():
    backend_root = Path(__file__).resolve().parents[2]
    playbook_path = backend_root / "agent_mold" / "playbooks" / "trading" / "delta_futures_manual_v1.md"

    playbook, cert = load_playbook_with_certification(playbook_path)
    assert playbook.metadata.playbook_id == "TRADING.DELTA.FUTURES.MANUAL.V1"
    assert playbook.metadata.output_contract == "trading_delta_futures_manual_v1"
    assert cert.certifiable is True
