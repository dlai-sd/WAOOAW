import pytest

from agent_mold.skills.playbook import ChannelName
from services.marketing_providers import MockChannelAdapter, ProviderAllowlist


def test_provider_allowlist_denies_unknown_channel(monkeypatch):
    monkeypatch.setenv("MARKETING_ALLOWED_CHANNELS", "linkedin")
    allowlist = ProviderAllowlist.from_env()

    allowlist.ensure_allowed(ChannelName.LINKEDIN)

    with pytest.raises(ValueError) as exc:
        allowlist.ensure_allowed(ChannelName.INSTAGRAM)

    assert "provider_not_allowed" in str(exc.value)


def test_social_provider_mock_returns_url_for_each_channel():
    for channel in [
        ChannelName.YOUTUBE,
        ChannelName.INSTAGRAM,
        ChannelName.FACEBOOK,
        ChannelName.LINKEDIN,
        ChannelName.WHATSAPP,
    ]:
        provider = MockChannelAdapter(channel=channel, base_url="https://example.test")
        result = provider.publish_text(text="hello", hashtags=["#WAOOAW"])
        assert result.provider_post_id
        assert result.provider_post_url.startswith("https://example.test/")
        assert f"/{channel.value}/" in result.provider_post_url
