from linux_arctis_manager.gui.view_models import (
    active_profile_name,
    dashboard_settings_summary,
    dashboard_summary,
    device_capability_summary,
    demo_status,
    flatten_status_values,
    mixer_levels,
    output_endpoint_summary,
    profile_workflow_summary,
    ready_output_endpoint_summary,
    routing_overview_summary,
    safe_percentage,
)


def test_flatten_status_values_extracts_nested_values():
    status = {
        'headset': {
            'headset_battery_charge': {'value': 87, 'type': 'percentage'},
            'headset_power_status': {'value': 'online', 'type': 'label'},
        },
        'gamedac': {
            'media_mix': {'value': 35, 'type': 'percentage'},
        },
    }

    assert flatten_status_values(status) == {
        'headset_battery_charge': 87,
        'headset_power_status': 'online',
        'media_mix': 35,
    }


def test_dashboard_summary_reports_status_and_outputs():
    status = {
        'headset': {
            'headset_battery_charge': {'value': 87, 'type': 'percentage'},
            'headset_power_status': {'value': 'online', 'type': 'label'},
            'mic_status': {'value': 'muted', 'type': 'label'},
        },
    }

    assert dashboard_summary(status) == {
        'device': 'online',
        'battery': '87%',
        'microphone': 'muted',
    }


def test_dashboard_summary_handles_empty_status():
    assert dashboard_summary({}) == {
        'device': 'No device detected',
        'battery': 'Unknown',
        'microphone': 'Unknown',
    }


def test_dashboard_settings_summary_reports_ready_outputs_and_active_profile():
    settings = {
        'profiles': {'active': 'Late Night'},
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
                'present': True,
            },
            {
                'node_name': 'Arctis_Media',
                'label': 'Media',
                'kind': 'sink',
                'implemented': True,
                'present': False,
            },
            {
                'node_name': 'Arctis_Microphone',
                'label': 'Microphone',
                'kind': 'source',
                'implemented': False,
                'present': False,
            },
        ],
    }

    assert dashboard_settings_summary(settings) == {
        'outputs': '2 ready: Game / Chat',
        'profile': 'Late Night',
    }


def test_dashboard_settings_summary_falls_back_to_catalog_and_default_profile():
    assert ready_output_endpoint_summary({}) == 'Game / Chat / Media / Aux'
    assert active_profile_name({}) == 'Default'
    assert dashboard_settings_summary({}) == {
        'outputs': 'Game / Chat / Media / Aux',
        'profile': 'Default',
    }


def test_ready_output_endpoint_summary_reports_when_no_outputs_are_ready():
    assert ready_output_endpoint_summary({
        'audio_endpoints': [
            {
                'node_name': 'Arctis_Game',
                'label': 'Game',
                'kind': 'sink',
                'implemented': True,
                'present': False,
            },
        ],
    }) == 'No virtual outputs ready'


def test_routing_overview_summary_reports_outputs_routes_and_planned_work():
    summary = routing_overview_summary({
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
            {
                'node_name': 'Arctis_Microphone',
                'label': 'Microphone',
                'kind': 'source',
                'implemented': False,
                'present': False,
            },
        ],
        'application_routes': [
            {
                'stream_index': 55,
                'application_name': 'Firefox',
                'current_endpoint_label': 'Game',
            },
        ],
    })

    assert summary['outputs_value'] == '1 ready / 1 missing'
    assert summary['outputs_detail'] == 'Ready: Game'
    assert summary['apps_value'] == '1 active stream'
    assert summary['apps_detail'] == 'Streams: Firefox -> Game'
    assert summary['planned_value'] == '1 planned endpoint'
    assert summary['planned_detail'] == 'Planned: Microphone source plus persistent app/game routing rules.'


def test_routing_overview_summary_handles_empty_metadata():
    summary = routing_overview_summary({})

    assert summary['outputs_value'] == 'Waiting'
    assert summary['outputs_detail'] == 'Catalog: Game / Chat / Media / Aux'
    assert summary['apps_value'] == 'No active streams'
    assert summary['planned_value'] == '1 planned endpoint'


def test_device_capability_summary_groups_supported_controls():
    summary = {
        capability['key']: capability
        for capability in device_capability_summary({
            'device': {
                'mic_volume': 80,
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
    }

    assert summary['microphone']['state'] == 'Supported'
    assert summary['microphone']['detail'] == 'Controls: Mic Volume / Sidetone'
    assert summary['noise_control']['state'] == 'Supported'
    assert summary['noise_control']['detail'] == 'Controls: ANC'
    assert summary['power_wireless']['state'] == 'Supported'
    assert summary['power_wireless']['detail'] == 'Controls: Wireless Mode'
    assert summary['audio_dac']['state'] == 'Not exposed'


def test_device_capability_summary_handles_no_device():
    summary = device_capability_summary({})

    assert {capability['state'] for capability in summary} == {'No device'}


def test_profile_workflow_summary_reports_saved_profiles_and_readiness():
    assert profile_workflow_summary({
        'device': {'mic_volume': 75},
        'profiles': {
            'available': ['Default', 'Late Night', 'Movie', 'Footsteps', 'Music'],
            'active': 'Movie',
        },
    }) == {
        'saved_value': '5 saved profiles',
        'saved_detail': 'Available: Default / Late Night / Movie / Footsteps / +1 more',
        'save_value': 'Ready',
        'save_detail': 'Save captures the currently exposed device settings for this headset.',
        'automation_value': 'Planned',
        'automation_detail': 'Future app/game switching will build on active app routes and profile metadata.',
    }


def test_profile_workflow_summary_handles_no_saved_profiles():
    assert profile_workflow_summary({}) == {
        'saved_value': 'No saved profiles',
        'saved_detail': 'Save the current device settings to start a per-device profile list.',
        'save_value': 'No device',
        'save_detail': 'Connect a supported headset before saving a profile.',
        'automation_value': 'Planned',
        'automation_detail': 'Future app/game switching will build on active app routes and profile metadata.',
    }


def test_mixer_levels_map_media_and_chat_mix_to_endpoint_groups():
    status = {
        'gamedac': {
            'media_mix': {'value': 35, 'type': 'percentage'},
            'chat_mix': {'value': 65, 'type': 'percentage'},
        },
    }

    assert mixer_levels(status) == {
        'Arctis_Game': 35,
        'Arctis_Chat': 65,
        'Arctis_Media': 35,
        'Arctis_Aux': 35,
        'Arctis_Microphone': 0,
    }


def test_safe_percentage_clamps_and_falls_back():
    assert safe_percentage(150) == 100
    assert safe_percentage(-10) == 0
    assert safe_percentage('45') == 45
    assert safe_percentage('bad', fallback=77) == 77


def test_output_endpoint_summary_only_lists_implemented_sinks():
    assert output_endpoint_summary() == 'Game / Chat / Media / Aux'


def test_demo_status_drives_dashboard_and_mixer_models():
    summary = dashboard_summary(demo_status())
    levels = mixer_levels(demo_status())

    assert summary['device'] == 'online'
    assert summary['battery'] == '87%'
    assert summary['microphone'] == 'unmuted'
    assert levels['Arctis_Game'] == 70
    assert levels['Arctis_Chat'] == 55
