import logging
import time
from typing import Any

import pulsectl

from linux_arctis_manager.audio_endpoints import (VIRTUAL_AUDIO_ENDPOINTS,
                                                  VIRTUAL_SINK_ENDPOINTS,
                                                  VIRTUAL_SINK_NODE_NAMES,
                                                  endpoints_for_mix_group)
from linux_arctis_manager.constants import STEELSERIES_VENDOR_ID

ONLY_PHYSICAL = 1
ONLY_VIRTUAL = 2
ALL_SINKS = 3

class TypedPulseSinkInfo(pulsectl.PulseSinkInfo):
    name: str


class TypedPulseSinkInputInfo(pulsectl.PulseSinkInputInfo):
    index: int
    name: str
    sink: int


class PulseAudioManager:
    _instance: 'PulseAudioManager|None' = None

    @staticmethod
    def get_instance() -> 'PulseAudioManager':
        if PulseAudioManager._instance is None:
            PulseAudioManager._instance = PulseAudioManager()

        return PulseAudioManager._instance

    def __init__(self):
        self.pulse = pulsectl.Pulse('linux-arctis-manager')
        self.logger = logging.getLogger('PulseAudioManager')
    
    def sink_list_wrapper(self) -> list[TypedPulseSinkInfo]:
        retry_attempts = 15

        sinks: list[TypedPulseSinkInfo] = []
        while retry_attempts > 0:
            try:
                sinks = self.pulse.sink_list()
                break
            except pulsectl.PulseError as e:
                self.logger.error(f'Error while getting sink list: {e}')
                retry_attempts -= 1
                time.sleep(1)

        sinks: list[TypedPulseSinkInfo] = sinks if type(sinks) is list else [sinks] # pyright: ignore[reportAssignmentType]

        return sinks
    
    def get_arctis_sinks(self, mode: int = ALL_SINKS, vendor_id: int = STEELSERIES_VENDOR_ID, product_id: int|list[int]|None = None) -> list[TypedPulseSinkInfo]:
        sinks = self.sink_list_wrapper()

        def check_prod_id(product_id_attr: str) -> bool:
            if product_id is None:
                return True

            lst = product_id if type(product_id) is list else [product_id]

            return product_id_attr in [f'0x{pid:04x}' for pid in lst]

        physical = [s for s in sinks if s.proplist.get('device.vendor.id', '') == f'0x{vendor_id:04x}' and check_prod_id(s.proplist.get('device.product.id', ''))]
        virtual = [s for s in sinks if s.proplist.get('node.name', '') in VIRTUAL_SINK_NODE_NAMES]

        if mode == ONLY_PHYSICAL:
            sinks = physical
        elif mode == ONLY_VIRTUAL:
            sinks = virtual
        else:
            sinks = physical + virtual

        return sinks

    def create_virtual_sink(self, name: str, description: str, sink_output: str) -> None:
        sink = next((s for s in self.get_arctis_sinks(ONLY_VIRTUAL) if s.proplist.get('node.name', '') == name), None)
        if sink:
            return
        
        self.logger.info(f'Creating virtual sink "{name}" -> "{sink_output}"...')
        escaped_node_description = description.replace(' ', '\\ ')
        self.pulse.module_load(
            'module-null-sink',
            f'sink_name={name} '
            f'sink_properties=node.description="{escaped_node_description}"'
        )

        self.pulse.module_load(
            'module-loopback',
            f'source={name}.monitor '
            f'sink={sink_output} '
            'latency_msec=0'
        )
    
    def remove_virtual_sink(self, name: str) -> None:
        sink = next((s for s in self.get_arctis_sinks(ONLY_VIRTUAL) if s.proplist.get('node.name', '') == name), None)
        if not sink:
            return
        
        self.logger.info(f'Removing virtual sink "{name}"...')
        modules = self.pulse.module_list()
        for module in modules:
            if module.argument and name in module.argument:
                self.pulse.module_unload(module.index)
    
    def wait_for_physical_device(self, vendor_id: int, product_id: int, attempts: int = 10) -> bool:
        vendor_id_hex = f'0x{vendor_id:04x}'
        product_id_hex = f'0x{product_id:04x}'

        while attempts > 0:
            if next((s for s in self.get_arctis_sinks(ONLY_PHYSICAL, vendor_id=vendor_id, product_id=product_id)), None):
                return True

            attempts -= 1
            time.sleep(1)
        
        self.logger.error(f'Failed to find SteelSeries Arctis device {vendor_id:04x}:{product_id:04x} after {attempts} attempts')

        return False

    def redirect_audio(self, output_sink_node_name: str) -> None:
        self.logger.info(f'Redirecting audio to {output_sink_node_name}...')

        sink = next((s for s in self.sink_list_wrapper() if s.proplist.get('node.nick', '') == output_sink_node_name or s.proplist.get('node.name', '') == output_sink_node_name), None)
        if sink is None:
            self.logger.error(f'Failed to find sink {output_sink_node_name} to set it as default')
            return
        self.pulse.default_set(sink)
    
    def get_default_device(self) -> TypedPulseSinkInfo|None:
        server_info = self.pulse.server_info()
        default_sink_name: str|None = getattr(server_info, 'default_sink_name', None)

        if default_sink_name is None:
            return None
        
        sink = next((s for s in self.sink_list_wrapper() if s.proplist.get('node.name', '') == default_sink_name), None)

        return sink

    def virtual_endpoint_statuses(self) -> list[dict[str, Any]]:
        try:
            sinks = self.pulse.sink_list()
        except pulsectl.PulseError as e:
            self.logger.warning('Failed to read virtual audio endpoints: %s', e)
            sinks = []

        if sinks is None:
            sinks = []
        sinks = sinks if type(sinks) is list else [sinks] # pyright: ignore[reportAssignmentType]
        sinks = [s for s in sinks if s.proplist.get('node.name', '') in VIRTUAL_SINK_NODE_NAMES]
        sinks_by_node_name = {s.proplist.get('node.name', ''): s for s in sinks}

        default_sink_name = None
        try:
            default_sink_name = getattr(self.pulse.server_info(), 'default_sink_name', None)
        except pulsectl.PulseError as e:
            self.logger.warning('Failed to read default PulseAudio sink: %s', e)

        result = []
        for endpoint in VIRTUAL_AUDIO_ENDPOINTS:
            sink = sinks_by_node_name.get(endpoint.node_name)
            result.append({
                'node_name': endpoint.node_name,
                'label': endpoint.label,
                'kind': endpoint.kind,
                'mix_group': endpoint.mix_group,
                'implemented': endpoint.implemented,
                'present': sink is not None,
                'default': sink is not None and sink.proplist.get('node.name', '') == default_sink_name,
                'description': sink.proplist.get('node.description', '') if sink else '',
            })

        return result

    def application_routes(self) -> list[dict[str, Any]]:
        try:
            sinks = self.pulse.sink_list()
            sink_inputs = self.pulse.sink_input_list()
        except pulsectl.PulseError as e:
            self.logger.warning('Failed to read active application routes: %s', e)
            return []

        if sinks is None:
            sinks = []
        if sink_inputs is None:
            sink_inputs = []

        sinks = sinks if type(sinks) is list else [sinks] # pyright: ignore[reportAssignmentType]
        sink_inputs = sink_inputs if type(sink_inputs) is list else [sink_inputs] # pyright: ignore[reportAssignmentType]

        sinks_by_index = {getattr(sink, 'index', -1): sink for sink in sinks}
        virtual_sinks_by_node_name = {
            sink.proplist.get('node.name', ''): sink
            for sink in sinks
            if sink.proplist.get('node.name', '') in VIRTUAL_SINK_NODE_NAMES
        }

        result = []
        for stream in sink_inputs:
            app_name = stream.proplist.get('application.name') or stream.proplist.get('application.process.binary')
            if not app_name:
                continue

            sink = sinks_by_index.get(getattr(stream, 'sink', -1))
            sink_node_name = sink.proplist.get('node.name', '') if sink else ''
            sink_description = sink.proplist.get('node.description', '') if sink else ''
            current_endpoint = next((
                endpoint
                for endpoint in VIRTUAL_SINK_ENDPOINTS
                if endpoint.node_name == sink_node_name
            ), None)

            result.append({
                'stream_index': getattr(stream, 'index', -1),
                'name': getattr(stream, 'name', '') or app_name,
                'application_name': app_name,
                'process_binary': stream.proplist.get('application.process.binary', ''),
                'process_id': stream.proplist.get('application.process.id', ''),
                'sink_index': getattr(stream, 'sink', -1),
                'sink_node_name': sink_node_name,
                'sink_description': sink_description,
                'current_endpoint_node_name': current_endpoint.node_name if current_endpoint else '',
                'current_endpoint_label': current_endpoint.label if current_endpoint else '',
                'routable': bool(virtual_sinks_by_node_name),
            })

        return result

    def move_application_route(self, stream_index: int, endpoint_node_name: str) -> bool:
        if endpoint_node_name not in VIRTUAL_SINK_NODE_NAMES:
            self.logger.warning('Refusing to route stream %s to unsupported endpoint %s', stream_index, endpoint_node_name)
            return False

        try:
            sinks = self.pulse.sink_list()
        except pulsectl.PulseError as e:
            self.logger.warning('Failed to read sinks before moving stream: %s', e)
            return False

        if sinks is None:
            sinks = []
        sinks = sinks if type(sinks) is list else [sinks] # pyright: ignore[reportAssignmentType]

        sink = next((
            sink
            for sink in sinks
            if sink.proplist.get('node.name', '') == endpoint_node_name
        ), None)
        if sink is None:
            self.logger.warning('Refusing to route stream %s because endpoint %s is missing', stream_index, endpoint_node_name)
            return False

        try:
            self.pulse.sink_input_move(stream_index, sink.index)
        except pulsectl.PulseError as e:
            self.logger.warning('Failed to route stream %s to %s: %s', stream_index, endpoint_node_name, e)
            return False

        return True

    def set_mix(self, media_mix: int, chat_mix: int):
        if media_mix > 100:
            media_mix = 100
        if chat_mix > 100:
            chat_mix = 100

        sinks = self.get_arctis_sinks(ONLY_VIRTUAL)

        sinks_by_node_name = {s.proplist.get('node.name', ''): s for s in sinks}

        for endpoint in endpoints_for_mix_group('media'):
            if sink := sinks_by_node_name.get(endpoint.node_name):
                self.pulse.volume_set_all_chans(sink, media_mix / 100)
        for endpoint in endpoints_for_mix_group('chat'):
            if sink := sinks_by_node_name.get(endpoint.node_name):
                self.pulse.volume_set_all_chans(sink, chat_mix / 100)

    def sinks_setup(self, device_name: str, vendor_id: int, product_id: int|list[int]|None):
        real_sink = self.get_arctis_sinks(ONLY_PHYSICAL, vendor_id=vendor_id, product_id=product_id)

        if not real_sink:
            self.logger.warning('No SteelSeries Arctis sink found.')
            return
        
        for endpoint in VIRTUAL_SINK_ENDPOINTS:
            self.create_virtual_sink(endpoint.node_name, f'{device_name} {endpoint.label}', real_sink[0].name)

    def sinks_teardown(self):
        self.logger.info('Removing virtual sinks...')

        for endpoint in VIRTUAL_SINK_ENDPOINTS:
            self.remove_virtual_sink(endpoint.node_name)
