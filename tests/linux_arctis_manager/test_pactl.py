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
    def __init__(self, node_name: str, description: str, index: int = 1):
        self.index = index
        self.name = node_name
        self.proplist = {
            'node.name': node_name,
            'node.description': description,
        }


class FakeSinkInput:
    def __init__(self, stream_index: int, sink_index: int, app_name: str):
        self.index = stream_index
        self.name = app_name
        self.sink = sink_index
        self.proplist = {
            'application.name': app_name,
            'application.process.binary': app_name.lower(),
            'application.process.id': '1234',
        }


class FakeServerInfo:
    default_sink_name = PULSE_GAME_NODE_NAME


class FakePulse:
    moved_stream = None

    def sink_list(self):
        return [
            FakeSink(PULSE_GAME_NODE_NAME, 'Arctis Game', 10),
            FakeSink(PULSE_CHAT_NODE_NAME, 'Arctis Chat', 11),
        ]

    def server_info(self):
        return FakeServerInfo()

    def sink_input_list(self):
        return [
            FakeSinkInput(55, 10, 'Firefox'),
            FakeSinkInput(56, 99, 'Music'),
        ]

    def sink_input_move(self, stream_index, sink_index):
        self.moved_stream = (stream_index, sink_index)


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


def test_application_routes_report_active_streams_and_current_endpoint():
    manager = object.__new__(PulseAudioManager)
    manager.pulse = FakePulse()
    manager.logger = logging.getLogger('test')

    routes = manager.application_routes()
    by_app = {route['application_name']: route for route in routes}

    assert by_app['Firefox']['stream_index'] == 55
    assert by_app['Firefox']['sink_node_name'] == PULSE_GAME_NODE_NAME
    assert by_app['Firefox']['current_endpoint_label'] == 'Game'
    assert by_app['Firefox']['routable'] is True
    assert by_app['Music']['sink_node_name'] == ''
    assert by_app['Music']['current_endpoint_label'] == ''


def test_move_application_route_uses_virtual_sink_index():
    manager = object.__new__(PulseAudioManager)
    manager.pulse = FakePulse()
    manager.logger = logging.getLogger('test')

    assert manager.move_application_route(55, PULSE_CHAT_NODE_NAME) is True
    assert manager.pulse.moved_stream == (55, 11)


def test_move_application_route_rejects_unknown_endpoint():
    manager = object.__new__(PulseAudioManager)
    manager.pulse = FakePulse()
    manager.logger = logging.getLogger('test')

    assert manager.move_application_route(55, 'Not_An_Endpoint') is False
    assert manager.pulse.moved_stream is None
