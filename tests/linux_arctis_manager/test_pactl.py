import logging

import pytest

from linux_arctis_manager.constants import (
    PULSE_CHAT_NODE_NAME,
    PULSE_GAME_NODE_NAME,
    PULSE_MEDIA_NODE_NAME,
    PULSE_MICROPHONE_NODE_NAME,
)

try:
    from linux_arctis_manager.pactl import PulseAudioManager
except FileNotFoundError as exc:
    pytest.skip(f'PulseAudio shared library is not available: {exc}', allow_module_level=True)


class FakeSink:
    def __init__(self, node_name: str, description: str):
        self.name = node_name
        self.proplist = {
            'node.name': node_name,
            'node.description': description,
        }


class FakeServerInfo:
    default_sink_name = PULSE_GAME_NODE_NAME


class FakePulse:
    def sink_list(self):
        return [
            FakeSink(PULSE_GAME_NODE_NAME, 'Arctis Game'),
            FakeSink(PULSE_CHAT_NODE_NAME, 'Arctis Chat'),
        ]

    def server_info(self):
        return FakeServerInfo()


def test_virtual_endpoint_statuses_report_present_missing_and_default_outputs():
    manager = object.__new__(PulseAudioManager)
    manager.pulse = FakePulse()
    manager.logger = logging.getLogger('test')

    statuses = manager.virtual_endpoint_statuses()
    by_node = {status['node_name']: status for status in statuses}

    assert by_node[PULSE_GAME_NODE_NAME]['present'] is True
    assert by_node[PULSE_GAME_NODE_NAME]['default'] is True
    assert by_node[PULSE_GAME_NODE_NAME]['description'] == 'Arctis Game'
    assert by_node[PULSE_CHAT_NODE_NAME]['present'] is True
    assert by_node[PULSE_CHAT_NODE_NAME]['default'] is False
    assert by_node[PULSE_MEDIA_NODE_NAME]['present'] is False
    assert by_node[PULSE_MICROPHONE_NODE_NAME]['implemented'] is False
    assert by_node[PULSE_MICROPHONE_NODE_NAME]['present'] is False
