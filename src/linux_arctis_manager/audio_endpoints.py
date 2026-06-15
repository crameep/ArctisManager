from dataclasses import dataclass
from typing import Literal

from linux_arctis_manager.constants import (
    PULSE_AUX_NODE_NAME,
    PULSE_CHAT_NODE_NAME,
    PULSE_GAME_NODE_NAME,
    PULSE_MEDIA_NODE_NAME,
    PULSE_MICROPHONE_NODE_NAME,
)

EndpointKind = Literal['sink', 'source']
MixGroup = Literal['media', 'chat', 'microphone']


@dataclass(frozen=True)
class VirtualAudioEndpoint:
    node_name: str
    label: str
    kind: EndpointKind
    mix_group: MixGroup
    implemented: bool = True


VIRTUAL_AUDIO_ENDPOINTS: tuple[VirtualAudioEndpoint, ...] = (
    VirtualAudioEndpoint(PULSE_GAME_NODE_NAME, 'Game', 'sink', 'media'),
    VirtualAudioEndpoint(PULSE_CHAT_NODE_NAME, 'Chat', 'sink', 'chat'),
    VirtualAudioEndpoint(PULSE_MEDIA_NODE_NAME, 'Media', 'sink', 'media'),
    VirtualAudioEndpoint(PULSE_AUX_NODE_NAME, 'Aux', 'sink', 'media'),
    VirtualAudioEndpoint(PULSE_MICROPHONE_NODE_NAME, 'Microphone', 'source', 'microphone', implemented=False),
)

VIRTUAL_SINK_ENDPOINTS = tuple(
    endpoint
    for endpoint in VIRTUAL_AUDIO_ENDPOINTS
    if endpoint.kind == 'sink' and endpoint.implemented
)

VIRTUAL_SINK_NODE_NAMES = tuple(endpoint.node_name for endpoint in VIRTUAL_SINK_ENDPOINTS)


def endpoints_for_mix_group(mix_group: MixGroup) -> tuple[VirtualAudioEndpoint, ...]:
    return tuple(
        endpoint
        for endpoint in VIRTUAL_SINK_ENDPOINTS
        if endpoint.mix_group == mix_group
    )
