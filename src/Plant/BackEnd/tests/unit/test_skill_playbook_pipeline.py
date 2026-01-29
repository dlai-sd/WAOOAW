from pathlib import Path

from agent_mold.skills.executor import execute_marketing_multichannel_v1
from agent_mold.skills.loader import load_playbook
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
    assert ChannelName.LINKEDIN in channels
    assert ChannelName.INSTAGRAM in channels

    linkedin = next(v for v in result.output.variants if v.channel == ChannelName.LINKEDIN)
    insta = next(v for v in result.output.variants if v.channel == ChannelName.INSTAGRAM)

    assert len(linkedin.text) <= 3000
    assert len(insta.text) <= 2200
    assert "#WAOOAW" in linkedin.text or "#WAOOAW" in " ".join(linkedin.hashtags)
