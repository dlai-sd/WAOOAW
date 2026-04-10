from agent_mold.skills.artifact_routing import route_artifact_requests
from agent_mold.skills.playbook import ArtifactRequest, ChannelName


def test_route_artifact_requests_accepts_supported_youtube_types() -> None:
    accepted, rejected = route_artifact_requests(
        ChannelName.YOUTUBE,
        [
            ArtifactRequest(artifact_type="table", prompt="Create a comparison table"),
            ArtifactRequest(artifact_type="video", prompt="Create a short video"),
        ],
    )

    assert [item.artifact_type.value for item in accepted] == ["table", "video"]
    assert rejected == []


def test_route_artifact_requests_rejects_unsupported_linkedin_audio() -> None:
    accepted, rejected = route_artifact_requests(
        ChannelName.LINKEDIN,
        [ArtifactRequest(artifact_type="audio", prompt="Create a voice clip")],
    )

    assert accepted == []
    assert len(rejected) == 1
    assert rejected[0].artifact_type.value == "audio"


def test_route_artifact_requests_allows_facebook_image_and_rejects_video_audio() -> None:
    accepted, rejected = route_artifact_requests(
        ChannelName.FACEBOOK,
        [
            ArtifactRequest(artifact_type="image", prompt="Create a static visual"),
            ArtifactRequest(artifact_type="video_audio", prompt="Create a narrated reel"),
        ],
    )

    assert [item.artifact_type.value for item in accepted] == ["image"]
    assert [item.artifact_type.value for item in rejected] == ["video_audio"]