from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

from agent_mold.skills.playbook import ArtifactRequest, ArtifactType, ChannelName


ALLOWED_ARTIFACTS = {
    ChannelName.YOUTUBE: {ArtifactType.TABLE, ArtifactType.IMAGE, ArtifactType.VIDEO, ArtifactType.VIDEO_AUDIO},
    ChannelName.FACEBOOK: {ArtifactType.TABLE, ArtifactType.IMAGE, ArtifactType.VIDEO},
    ChannelName.LINKEDIN: {ArtifactType.TABLE, ArtifactType.IMAGE, ArtifactType.VIDEO},
    ChannelName.INSTAGRAM: {ArtifactType.IMAGE, ArtifactType.VIDEO},
    ChannelName.WHATSAPP: {ArtifactType.TABLE, ArtifactType.IMAGE, ArtifactType.AUDIO, ArtifactType.VIDEO, ArtifactType.VIDEO_AUDIO},
}


@dataclass(frozen=True)
class ArtifactRoutingFailure:
    artifact_type: ArtifactType
    reason: str


def route_artifact_requests(
    channel: ChannelName,
    requests: Iterable[ArtifactRequest],
) -> Tuple[List[ArtifactRequest], List[ArtifactRoutingFailure]]:
    allowed_types = ALLOWED_ARTIFACTS.get(channel, {ArtifactType.TABLE})
    accepted: List[ArtifactRequest] = []
    rejected: List[ArtifactRoutingFailure] = []

    for request in requests:
        if request.artifact_type not in allowed_types:
            rejected.append(
                ArtifactRoutingFailure(
                    artifact_type=request.artifact_type,
                    reason=f"{request.artifact_type.value} is not supported for channel {channel.value}",
                )
            )
            continue
        accepted.append(request)

    return accepted, rejected