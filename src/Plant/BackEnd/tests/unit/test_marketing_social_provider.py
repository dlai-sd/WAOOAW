from agent_mold.skills.playbook import ChannelName
from services.marketing_providers import MockChannelAdapter, RoutedSocialProvider, default_social_provider


def test_social_provider_routes_publish_for_each_channel():
    provider = default_social_provider()

    for channel in [
        ChannelName.YOUTUBE,
        ChannelName.INSTAGRAM,
        ChannelName.FACEBOOK,
        ChannelName.LINKEDIN,
        ChannelName.WHATSAPP,
    ]:
        result = provider.publish_text(channel=channel, text="hello", hashtags=["#WAOOAW"])
        assert result.provider_post_id
        assert result.provider_post_url
        assert f"/{channel.value}/" in result.provider_post_url


def test_social_provider_missing_adapter_raises():
    provider = RoutedSocialProvider(
        {
            ChannelName.LINKEDIN: MockChannelAdapter(channel=ChannelName.LINKEDIN, base_url="https://example.test"),
        }
    )

    result = provider.publish_text(channel=ChannelName.LINKEDIN, text="hi", hashtags=[])
    assert result.provider_post_url.startswith("https://example.test/")

    try:
        provider.publish_text(channel=ChannelName.INSTAGRAM, text="hi", hashtags=[])
        assert False, "Expected missing adapter to raise"
    except ValueError as exc:
        assert "provider_adapter_missing" in str(exc)
