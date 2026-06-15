import logging
import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest

pytest.importorskip('PySide6')

from PySide6.QtWidgets import QApplication

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
    assert window_app.mixer_sliders['Arctis_Chat'].value() == 55
    assert window_app.mixer_sliders['Arctis_Microphone'].value() == 0

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

    window_app._on_save_profile_clicked()
    window_app._on_load_profile_clicked()

    assert fake_dbus.saved_profile == 'Late Night'
    assert fake_dbus.loaded_profile == 'Late Night'

    window_app.sig_stop()
