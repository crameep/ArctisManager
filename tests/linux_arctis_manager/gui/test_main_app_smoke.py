import logging
import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest

pytest.importorskip('PySide6')

from PySide6.QtWidgets import QApplication, QSlider

from linux_arctis_manager.gui.main_app import QMainApp


def test_demo_main_window_opens_with_dashboard_and_mixer_content():
    app = QApplication.instance() or QApplication([])
    window_app = QMainApp(app, logging.CRITICAL, demo_mode=True)

    window_app.main_window.show()
    app.processEvents()

    assert window_app.header_title.text() == 'Dashboard'
    assert window_app.dashboard_cards['device'].text() == 'online'
    assert window_app.dashboard_cards['battery'].text() == '87%'
    assert window_app.dashboard_cards['microphone'].text() == 'unmuted'
    assert window_app.dashboard_cards['outputs'].text() == 'Game / Chat / Media / Aux'

    window_app.switch_panel('mixer')
    app.processEvents()

    assert window_app.header_title.text() == 'Mixer'
    assert window_app.mixer_sliders['Arctis_Game'].value() == 70
    assert window_app.mixer_value_labels['Arctis_Game'].text() == '70%'
    assert window_app.mixer_state_labels['Arctis_Game'].text() == 'Demo'
    assert window_app.mixer_sliders['Arctis_Chat'].value() == 55
    assert window_app.mixer_value_labels['Arctis_Chat'].text() == '55%'
    assert window_app.mixer_sliders['Arctis_Microphone'].value() == 0
    assert window_app.mixer_value_labels['Arctis_Microphone'].text() == '0%'
    assert window_app.mixer_state_labels['Arctis_Microphone'].text() == 'Planned'
    assert window_app.chatmix_balance_value_label.text() == 'Game/Media/Aux 70% / Chat 55%'
    assert window_app.chatmix_balance_detail_label.text() == 'Game, Media, and Aux follow media mix; Chat follows chat mix.'
    assert window_app.chatmix_media_balance_slider.findChild(QSlider).value() == 70
    assert window_app.chatmix_chat_balance_slider.findChild(QSlider).value() == 55

    window_app.sig_stop()


def test_profiles_page_updates_from_settings_metadata():
    app = QApplication.instance() or QApplication([])
    window_app = QMainApp(app, logging.CRITICAL, demo_mode=True)

    class FakeDbusWrapper:
        saved_profile = ''
        loaded_profile = ''

        def save_profile(self, name):
            self.saved_profile = name

        def load_profile(self, name):
            self.loaded_profile = name

        def stop(self):
            pass

    fake_dbus = FakeDbusWrapper()
    window_app.dbus_wrapper = fake_dbus
    window_app.on_settings_received({
        'device': {'sidetone': 6},
        'profiles': {
            'available': ['Default', 'Late Night'],
            'active': 'Late Night',
        },
    })
    app.processEvents()

    assert window_app.active_profile_label.text() == 'Late Night'
    assert window_app.profile_name_input.text() == 'Late Night'
    assert window_app.save_profile_button.isEnabled()
    assert window_app.load_profile_button.isEnabled()
    assert window_app.profile_combo.currentText() == 'Late Night'
    assert window_app.profile_overview_value_labels['saved'].text() == '2 saved profiles'
    assert window_app.profile_overview_detail_labels['saved'].text() == 'Available: Default / Late Night'
    assert window_app.profile_overview_value_labels['save'].text() == 'Ready'
    assert window_app.profile_overview_value_labels['automation'].text() == 'Planned'

    window_app._on_save_profile_clicked()
    window_app._on_load_profile_clicked()

    assert fake_dbus.saved_profile == 'Late Night'
    assert fake_dbus.loaded_profile == 'Late Night'

    window_app.sig_stop()


def test_routing_page_updates_from_audio_endpoint_metadata():
    app = QApplication.instance() or QApplication([])
    window_app = QMainApp(app, logging.CRITICAL, demo_mode=True)

    class FakeDbusWrapper:
        requested_settings = False
        moved_route = None

        def request_settings(self):
            self.requested_settings = True

        def move_application_route(self, stream_index, endpoint_node_name):
            self.moved_route = (stream_index, endpoint_node_name)

        def stop(self):
            pass

    fake_dbus = FakeDbusWrapper()
    window_app.dbus_wrapper = fake_dbus
    window_app.on_settings_received({
        'audio_endpoints': [
            {
                'node_name': 'Arctis_Game',
                'label': 'Game',
                'kind': 'sink',
                'mix_group': 'media',
                'implemented': True,
                'present': True,
                'default': True,
                'description': 'Nova Game',
            },
            {
                'node_name': 'Arctis_Chat',
                'label': 'Chat',
                'kind': 'sink',
                'mix_group': 'chat',
                'implemented': True,
                'present': False,
                'default': False,
                'description': '',
            },
            {
                'node_name': 'Arctis_Media',
                'label': 'Media',
                'kind': 'sink',
                'mix_group': 'media',
                'implemented': True,
                'present': False,
                'default': False,
                'description': '',
            },
            {
                'node_name': 'Arctis_Aux',
                'label': 'Aux',
                'kind': 'sink',
                'mix_group': 'media',
                'implemented': True,
                'present': False,
                'default': False,
                'description': '',
            },
            {
                'node_name': 'Arctis_Microphone',
                'label': 'Microphone',
                'kind': 'source',
                'mix_group': 'microphone',
                'implemented': False,
                'present': False,
                'default': False,
                'description': '',
            },
        ],
        'application_routes': [
            {
                'stream_index': 55,
                'name': 'Firefox',
                'application_name': 'Firefox',
                'process_binary': 'firefox',
                'process_id': '1234',
                'sink_index': 1,
                'sink_node_name': 'Arctis_Game',
                'sink_description': 'Nova Game',
                'current_endpoint_node_name': 'Arctis_Game',
                'current_endpoint_label': 'Game',
                'routable': True,
            },
        ],
    })
    window_app.switch_panel('routing')
    app.processEvents()

    assert window_app.routing_status_label.text() == '1 virtual outputs ready, 3 missing.'
    assert window_app.routing_overview_value_labels['outputs'].text() == '1 ready / 3 missing'
    assert window_app.routing_overview_detail_labels['outputs'].text() == 'Ready: Game'
    assert window_app.routing_overview_value_labels['apps'].text() == '1 active stream'
    assert window_app.routing_overview_detail_labels['apps'].text() == 'Streams: Firefox -> Game'
    assert window_app.routing_overview_value_labels['planned'].text() == '1 planned endpoint'
    assert window_app.routing_state_labels['Arctis_Game'].text() == 'Ready / Default'
    assert window_app.routing_detail_labels['Arctis_Game'].text() == 'Virtual output present: Nova Game'
    assert window_app.routing_state_labels['Arctis_Chat'].text() == 'Missing'
    assert window_app.routing_state_labels['Arctis_Microphone'].text() == 'Planned'
    assert window_app.mixer_state_labels['Arctis_Game'].text() == 'Ready / Default'
    assert window_app.mixer_detail_labels['Arctis_Game'].text() == 'Output present: Nova Game'
    assert window_app.mixer_state_labels['Arctis_Chat'].text() == 'Missing'
    assert window_app.mixer_detail_labels['Arctis_Chat'].text() == 'Virtual output not available yet.'
    assert window_app.mixer_state_labels['Arctis_Microphone'].text() == 'Planned'
    assert window_app.route_app_stream_combo.currentData() == 55
    assert window_app.route_endpoint_combo.currentData() == 'Arctis_Game'
    assert window_app.assign_route_button.isEnabled()
    assert window_app.application_route_status_label.text() == '1 active app stream(s) can be assigned.'

    window_app._on_refresh_routing_clicked()
    window_app._on_assign_route_clicked()

    assert fake_dbus.requested_settings is True
    assert fake_dbus.moved_route == (55, 'Arctis_Game')

    window_app.sig_stop()


def test_device_page_updates_capability_overview_from_settings_metadata():
    app = QApplication.instance() or QApplication([])
    window_app = QMainApp(app, logging.CRITICAL, demo_mode=True)

    window_app.on_settings_received({
        'device': {
            'mic_volume': 82,
            'mic_side_tone': 2,
            'noise_cancelling': 1,
            'wireless_mode': 0,
        },
        'settings_config': {
            'mic_volume': {'type': 'slider'},
            'mic_side_tone': {'type': 'discrete_map'},
            'noise_cancelling': {'type': 'discrete_map'},
            'wireless_mode': {'type': 'discrete_map'},
        },
    })
    window_app.switch_panel('device')
    app.processEvents()

    assert window_app.device_capability_state_labels['microphone'].text() == 'Supported'
    assert window_app.device_capability_detail_labels['microphone'].text() == 'Controls: Mic Volume / Sidetone'
    assert window_app.device_capability_state_labels['noise_control'].text() == 'Supported'
    assert window_app.device_capability_detail_labels['noise_control'].text() == 'Controls: ANC'
    assert window_app.device_capability_state_labels['power_wireless'].text() == 'Supported'
    assert window_app.device_capability_detail_labels['power_wireless'].text() == 'Controls: Wireless Mode'
    assert window_app.device_capability_state_labels['audio_dac'].text() == 'Not exposed'

    window_app.sig_stop()


def test_settings_page_shows_setup_guidance_and_service_state():
    app = QApplication.instance() or QApplication([])
    window_app = QMainApp(app, logging.CRITICAL, demo_mode=True)

    window_app.switch_panel('settings')
    app.processEvents()

    assert window_app.service_status_label.text() == 'Demo mode - D-Bus disabled'
    assert window_app.service_detail_label.text() == 'Demo mode previews the redesigned GUI without touching the user service or headset.'
    assert window_app.setup_state_labels['dbus'].text() == 'Demo'
    assert window_app.setup_state_labels['udev'].text() == 'Required'
    assert window_app.setup_state_labels['audio'].text() == 'Required'
    assert window_app.setup_state_labels['autostart'].text() == 'Optional'
    assert 'lam-cli setup' in window_app.setup_detail_labels['udev'].text()
    assert 'PulseAudio compatibility API' in window_app.setup_detail_labels['audio'].text()

    window_app.on_settings_received({
        'device': {'mic_volume': 80},
        'settings_config': {'mic_volume': {'type': 'slider'}},
    })
    app.processEvents()

    assert window_app.service_status_label.text() == 'D-Bus settings connected'
    assert window_app.setup_state_labels['dbus'].text() == 'Connected'

    window_app.sig_stop()


def test_dashboard_uses_settings_for_profile_and_output_readiness():
    app = QApplication.instance() or QApplication([])
    window_app = QMainApp(app, logging.CRITICAL, demo_mode=True)

    window_app.on_settings_received({
        'profiles': {
            'available': ['Default', 'Movie Night'],
            'active': 'Movie Night',
        },
        'audio_endpoints': [
            {
                'node_name': 'Arctis_Game',
                'label': 'Game',
                'kind': 'sink',
                'implemented': True,
                'present': True,
            },
            {
                'node_name': 'Arctis_Chat',
                'label': 'Chat',
                'kind': 'sink',
                'implemented': True,
                'present': False,
            },
        ],
    })
    window_app.on_status_received({
        'headset': {
            'headset_power_status': {'value': 'online', 'type': 'label'},
            'headset_battery_charge': {'value': 91, 'type': 'percentage'},
        },
    })
    app.processEvents()

    assert window_app.dashboard_cards['device'].text() == 'online'
    assert window_app.dashboard_cards['battery'].text() == '91%'
    assert window_app.dashboard_cards['outputs'].text() == '1 ready: Game'
    assert window_app.dashboard_cards['profile'].text() == 'Movie Night'

    window_app.sig_stop()
