import json
from types import SimpleNamespace

from linux_arctis_manager.dbus_service import ArctisManagerDbusSettingsService


def test_settings_payload_includes_connected_device_identity():
    core = SimpleNamespace(
        device_config=SimpleNamespace(name='SteelSeries Arctis Nova 7', settings={}),
        usb_device=SimpleNamespace(idVendor=0x1038, idProduct=0x2202),
        general_settings=SimpleNamespace(settings_config=[], to_dict=lambda: {}),
        device_settings=SimpleNamespace(settings={}),
        pa_audio_manager=SimpleNamespace(),
    )
    service = ArctisManagerDbusSettingsService(core)
    service._profile_metadata = lambda: {'available': [], 'active': 'Default'}
    service._audio_endpoint_metadata = lambda: []
    service._application_route_metadata = lambda: []

    payload = json.loads(service.settings_to_json(
        core.general_settings,
        core.device_config,
        core.device_settings,
    ))

    assert payload['device_info'] == {
        'name': 'SteelSeries Arctis Nova 7',
        'vendor_id': '1038',
        'product_id': '2202',
    }
