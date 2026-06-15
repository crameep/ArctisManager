from linux_arctis_manager.audio_endpoints import (
    VIRTUAL_AUDIO_ENDPOINTS,
    VIRTUAL_SINK_ENDPOINTS,
    VIRTUAL_SINK_NODE_NAMES,
    endpoints_for_mix_group,
)
from linux_arctis_manager.constants import (
    PULSE_AUX_NODE_NAME,
    PULSE_CHAT_NODE_NAME,
    PULSE_GAME_NODE_NAME,
    PULSE_MEDIA_NODE_NAME,
    PULSE_MICROPHONE_NODE_NAME,
)


def test_sonar_style_endpoint_catalog_includes_expected_channels():
    assert [endpoint.node_name for endpoint in VIRTUAL_AUDIO_ENDPOINTS] == [
        PULSE_GAME_NODE_NAME,
        PULSE_CHAT_NODE_NAME,
        PULSE_MEDIA_NODE_NAME,
        PULSE_AUX_NODE_NAME,
        PULSE_MICROPHONE_NODE_NAME,
    ]


def test_virtual_sink_endpoints_are_the_implemented_outputs():
    assert VIRTUAL_SINK_NODE_NAMES == (
        PULSE_GAME_NODE_NAME,
        PULSE_CHAT_NODE_NAME,
        PULSE_MEDIA_NODE_NAME,
        PULSE_AUX_NODE_NAME,
    )
    assert all(endpoint.kind == 'sink' for endpoint in VIRTUAL_SINK_ENDPOINTS)


def test_media_mix_group_covers_non_chat_outputs():
    assert [endpoint.node_name for endpoint in endpoints_for_mix_group('media')] == [
        PULSE_GAME_NODE_NAME,
        PULSE_MEDIA_NODE_NAME,
        PULSE_AUX_NODE_NAME,
    ]


def test_chat_mix_group_only_covers_chat_output():
    assert [endpoint.node_name for endpoint in endpoints_for_mix_group('chat')] == [
        PULSE_CHAT_NODE_NAME,
    ]
