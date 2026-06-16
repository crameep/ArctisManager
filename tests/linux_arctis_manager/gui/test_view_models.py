from linux_arctis_manager.gui.view_models import (
    active_profile_name,
    application_route_rows,
    chatmix_balance_summary,
    connected_device_name,
    dashboard_control_surface_summary,
    dashboard_detail_summary,
    dashboard_settings_summary,
    dashboard_summary,
    device_capability_summary,
    device_control_snapshot,
    demo_settings,
    demo_status,
    flatten_status_values,
    header_context_summary,
    mixer_levels,
    mixer_overview_summary,
    output_endpoint_readiness_detail,
    output_endpoint_summary,
    profile_app_context_summary,
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


def test_dashboard_summary_prefers_connected_device_name_from_settings():
    status = {
        'headset': {
            'headset_power_status': {'value': 'online', 'type': 'label'},
            'headset_battery_charge': {'value': 87, 'type': 'percentage'},
        },
    }
    settings = {
        'device_info': {
            'name': 'SteelSeries Arctis Nova 7',
            'vendor_id': '1038',
            'product_id': '2202',
        },
    }

    assert connected_device_name(settings) == 'SteelSeries Arctis Nova 7'
    assert dashboard_summary(status, settings)['device'] == 'SteelSeries Arctis Nova 7'


def test_dashboard_summary_handles_empty_status():
    assert dashboard_summary({}) == {
        'device': 'No device detected',
        'battery': 'Unknown',
        'microphone': 'Unknown',
    }


def test_header_context_summary_reports_persistent_page_context():
    assert header_context_summary(demo_status(), demo_settings()) == {
        'device': 'Arctis Nova 7 Wireless (demo)',
        'battery': '87%',
        'profile': 'Late Night',
        'outputs': '3 ready: Game / Chat / Media',
    }


def test_header_context_summary_handles_empty_metadata():
    assert header_context_summary({}, {}) == {
        'device': 'No device detected',
        'battery': 'Unknown',
        'profile': 'Default',
        'outputs': 'Game / Chat / Media / Aux',
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
        'device_info': {
            'name': 'SteelSeries Arctis Nova Pro Wireless',
            'vendor_id': '1038',
            'product_id': '12e0',
        },
    }

    assert dashboard_settings_summary(settings) == {
        'device': 'SteelSeries Arctis Nova Pro Wireless',
        'outputs': '2 ready: Game / Chat',
        'profile': 'Late Night',
    }


def test_dashboard_settings_summary_falls_back_to_catalog_and_default_profile():
    assert ready_output_endpoint_summary({}) == 'Game / Chat / Media / Aux'
    assert output_endpoint_readiness_detail({}) == 'Catalog: Game / Chat / Media / Aux | Planned: Microphone'
    assert active_profile_name({}) == 'Default'
    assert dashboard_settings_summary({}) == {
        'outputs': 'Game / Chat / Media / Aux',
        'profile': 'Default',
    }


def test_dashboard_detail_summary_reports_identity_status_outputs_and_profiles():
    settings = {
        'device_info': {
            'name': 'SteelSeries Arctis Nova 7',
            'vendor_id': '1038',
            'product_id': '2202',
        },
        'profiles': {
            'available': ['Default', 'Footsteps', 'Movie'],
            'active': 'Footsteps',
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
            {
                'node_name': 'Arctis_Microphone',
                'label': 'Microphone',
                'kind': 'source',
                'implemented': False,
                'present': False,
            },
        ],
    }
    status = {
        'headset': {
            'headset_power_status': {'value': 'online', 'type': 'label'},
            'headset_battery_charge': {'value': 91, 'type': 'percentage'},
        },
        'mic': {
            'mic_status': {'value': 'muted', 'type': 'label'},
        },
    }

    assert dashboard_detail_summary(status, settings) == {
        'device': 'USB 1038:2202',
        'battery': 'Power state: online',
        'microphone': 'Mute state: muted',
        'outputs': 'Ready: Game | Missing: Chat | Planned: Microphone',
        'profile': 'Saved: Default / Footsteps / Movie',
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


def test_application_route_rows_format_stream_metadata():
    assert application_route_rows({
        'application_routes': [
            {
                'stream_index': 55,
                'application_name': 'Firefox',
                'process_binary': 'firefox',
                'process_id': '1234',
                'current_endpoint_label': 'Game',
            },
            {
                'stream_index': 'not-an-int',
                'application_name': 'Ignored',
            },
        ],
    }) == [
        {
            'stream_index': 55,
            'title': 'Firefox',
            'current': 'Game',
            'detail': 'firefox | PID 1234 | Stream 55',
        },
    ]


def test_profile_app_context_summary_reports_active_routes():
    assert profile_app_context_summary({
        'application_routes': [
            {
                'stream_index': 55,
                'application_name': 'Firefox',
                'current_endpoint_label': 'Game',
            },
            {
                'stream_index': 56,
                'application_name': 'Discord',
                'current_endpoint_label': 'Chat',
            },
        ],
    }) == {
        'value': '2 active apps',
        'detail': 'Context: Firefox -> Game / Discord -> Chat',
    }


def test_profile_app_context_summary_handles_no_active_routes():
    assert profile_app_context_summary({}) == {
        'value': 'No active streams',
        'detail': 'Open audio apps will appear here before app/game profile switching is implemented.',
    }


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


def test_device_control_snapshot_reports_current_exposed_values():
    summary = {
        snapshot['key']: snapshot
        for snapshot in device_control_snapshot({
            'device': {
                'mic_volume': 80,
                'mic_side_tone': 2,
                'noise_cancelling': 1,
                'transparent_noise_cancelling_level': 4,
                'wireless_mode': 0,
                'auto_off_time_minutes': 30,
                'station_volume': 60,
                'gain': 1,
            },
            'settings_config': {
                'noise_cancelling': {
                    'values_mapping': {
                        '1': 'on',
                    },
                },
            },
        })
    }

    assert summary['microphone']['state'] == 'Ready'
    assert summary['microphone']['detail'] == 'Mic Volume: 80% / Sidetone: 2'
    assert summary['noise_control']['state'] == 'Ready'
    assert summary['noise_control']['detail'] == 'ANC: On / Transparency: 4%'
    assert summary['power_wireless']['state'] == 'Ready'
    assert summary['power_wireless']['detail'] == 'Wireless Mode: 0 / Auto Off: 30 min'
    assert summary['audio_dac']['state'] == 'Ready'
    assert summary['audio_dac']['detail'] == 'Station Volume: 60% / Gain: 1'


def test_device_control_snapshot_handles_no_device():
    summary = device_control_snapshot({})

    assert {snapshot['state'] for snapshot in summary} == {'No device'}


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


def test_mixer_overview_summary_reports_channel_state_and_mix_groups():
    assert mixer_overview_summary({
        'audio_endpoints': [
            {
                'node_name': 'Arctis_Game',
                'label': 'Game',
                'kind': 'sink',
                'mix_group': 'media',
                'implemented': True,
                'present': True,
            },
            {
                'node_name': 'Arctis_Chat',
                'label': 'Chat',
                'kind': 'sink',
                'mix_group': 'chat',
                'implemented': True,
                'present': True,
            },
            {
                'node_name': 'Arctis_Media',
                'label': 'Media',
                'kind': 'sink',
                'mix_group': 'media',
                'implemented': True,
                'present': False,
            },
            {
                'node_name': 'Arctis_Aux',
                'label': 'Aux',
                'kind': 'sink',
                'mix_group': 'media',
                'implemented': True,
                'present': False,
            },
            {
                'node_name': 'Arctis_Microphone',
                'label': 'Microphone',
                'kind': 'source',
                'mix_group': 'microphone',
                'implemented': False,
                'present': False,
            },
        ],
    }) == {
        'channels_value': '2 ready / 2 missing / 1 planned',
        'channels_detail': 'Ready: Game / Chat | Missing: Media / Aux | Planned: Microphone',
        'media_value': 'Game / Media / Aux',
        'media_detail': 'Media mix drives Game, Media, and Aux channels.',
        'chat_value': 'Chat',
        'chat_detail': 'Chat mix drives voice chat separately when the headset reports ChatMix.',
    }


def test_mixer_overview_summary_handles_missing_endpoint_metadata():
    assert mixer_overview_summary({}) == {
        'channels_value': 'Waiting',
        'channels_detail': 'Catalog: Game / Chat / Media / Aux | Planned: Microphone',
        'media_value': 'Game / Media / Aux',
        'media_detail': 'Media mix drives Game, Media, and Aux channels.',
        'chat_value': 'Chat',
        'chat_detail': 'Chat mix drives voice chat separately when the headset reports ChatMix.',
    }


def test_chatmix_balance_summary_reports_media_and_chat_groups():
    assert chatmix_balance_summary({
        'gamedac': {
            'media_mix': {'value': 35, 'type': 'percentage'},
            'chat_mix': {'value': 65, 'type': 'percentage'},
        },
    }) == {
        'value': 'Game/Media/Aux 35% / Chat 65%',
        'detail': 'Game, Media, and Aux follow media mix; Chat follows chat mix.',
        'media_level': 35,
        'chat_level': 65,
    }


def test_chatmix_balance_summary_handles_missing_mix_status():
    assert chatmix_balance_summary({}) == {
        'value': 'Waiting',
        'detail': 'Waiting for media_mix and chat_mix status values from the headset or GameDAC.',
        'media_level': 100,
        'chat_level': 100,
    }


def test_dashboard_control_surface_summary_reports_mix_routes_and_controls():
    assert dashboard_control_surface_summary(demo_status(), demo_settings()) == [
        {
            'key': 'mix',
            'title': 'ChatMix',
            'state': 'Ready',
            'detail': 'Game/Media/Aux 70% / Chat 55%. Game, Media, and Aux follow media mix; Chat follows chat mix.',
        },
        {
            'key': 'routes',
            'title': 'App Routes',
            'state': '2 active streams',
            'detail': 'Streams: Firefox -> Game / Discord -> Chat',
        },
        {
            'key': 'controls',
            'title': 'Device Controls',
            'state': '4 supported areas',
            'detail': 'Available: Microphone / Noise Control / Power & Wireless / Audio & DAC',
        },
    ]


def test_dashboard_control_surface_summary_handles_no_device():
    assert dashboard_control_surface_summary({}, {}) == [
        {
            'key': 'mix',
            'title': 'ChatMix',
            'state': 'Waiting',
            'detail': 'Waiting for media_mix and chat_mix status values from the headset or GameDAC.',
        },
        {
            'key': 'routes',
            'title': 'App Routes',
            'state': 'No active streams',
            'detail': 'Open audio apps will appear here when PulseAudio/PipeWire-pulse reports active playback streams.',
        },
        {
            'key': 'controls',
            'title': 'Device Controls',
            'state': 'No device',
            'detail': 'Connect a supported headset to expose device controls.',
        },
    ]


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


def test_demo_settings_drives_dashboard_routing_and_profiles():
    settings = demo_settings()

    assert dashboard_settings_summary(settings) == {
        'device': 'Arctis Nova 7 Wireless (demo)',
        'outputs': '3 ready: Game / Chat / Media',
        'profile': 'Late Night',
    }
    assert routing_overview_summary(settings)['outputs_value'] == '3 ready / 1 missing'
    assert routing_overview_summary(settings)['apps_value'] == '2 active streams'
    assert profile_workflow_summary(settings)['saved_value'] == '3 saved profiles'
    assert application_route_rows(settings)[0] == {
        'stream_index': 55,
        'title': 'Firefox',
        'current': 'Game',
        'detail': 'firefox | PID 1234 | Stream 55',
    }
