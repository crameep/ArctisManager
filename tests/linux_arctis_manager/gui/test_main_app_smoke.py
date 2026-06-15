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
