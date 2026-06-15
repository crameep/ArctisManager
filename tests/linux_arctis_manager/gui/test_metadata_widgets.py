import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest

pytest.importorskip('PySide6')

from PySide6.QtWidgets import QApplication, QLabel

from linux_arctis_manager.gui.settings_widget import QSettingsWidget
from linux_arctis_manager.gui.status_widget import QStatusWidget


def _app():
    return QApplication.instance() or QApplication([])


def test_status_widget_renders_dbus_status_payload():
    app = _app()
    widget = QStatusWidget(None)
    widget.update_status({
        'headset': {
            'headset_power_status': {'value': 'online', 'type': 'label'},
            'headset_battery_charge': {'value': 87, 'type': 'percentage'},
        },
    })
    app.processEvents()

    labels = [label.text() for label in widget.findChildren(QLabel)]

    assert 'Headset' in labels
    assert 'Headset Power Status: Online' in labels
    assert 'Headset Battery Charge: 87%' in labels


def test_settings_widget_renders_dbus_settings_metadata():
    app = _app()
    widget = QSettingsWidget(None, 'general', 'general')
    widget.update_settings({
        'general': {
            'redirect_audio_on_connect': True,
            'volume_preview': 7,
        },
        'settings_config': {
            'redirect_audio_on_connect': {
                'type': 'toggle',
                'default_value': False,
                'values': {
                    'on': True,
                    'off': False,
                    'off_label': 'off',
                    'on_label': 'on',
                },
            },
            'volume_preview': {
                'type': 'slider',
                'default_value': 5,
                'min': 0,
                'max': 10,
                'step': 1,
            },
        },
    })
    app.processEvents()

    labels = [label.text() for label in widget.findChildren(QLabel)]

    assert 'General' in labels
    assert 'Redirect Audio on Connect' in labels
    assert 'volume_preview' in labels
