from linux_arctis_manager.audio_endpoints import VIRTUAL_AUDIO_ENDPOINTS

StatusPayload = dict[str, dict[str, dict[str, str | int]]]

DEVICE_SETTING_LABELS = {
    'auto_off_time_minutes': 'Auto Off',
    'bluetooth_auto_mute': 'Bluetooth Auto Mute',
    'bluetooth_default': 'Bluetooth Power-Up',
    'bluetooth_power_status': 'Bluetooth Power',
    'bluetooth_powerup_state': 'Bluetooth Power-Up',
    'gain': 'Gain',
    'line_out': 'Line Out',
    'mic_led_brightness': 'Mic LED',
    'mic_mute_led_brightness': 'Mic Mute LED',
    'mic_side_tone': 'Sidetone',
    'mic_sidetone_boom': 'Boom Sidetone',
    'mic_sidetone_ear': 'Ear Sidetone',
    'mic_volume': 'Mic Volume',
    'noise_cancelling': 'ANC',
    'noise_cancelling_level': 'ANC Level',
    'pm_shutdown': 'Power Timeout',
    'sidetone': 'Sidetone',
    'station_home_screen_options': 'Home Screen Options',
    'station_home_screen_view': 'Home Screen',
    'station_screen_brightness': 'Screen Brightness',
    'station_screen_saver_timeout': 'Screen Saver Timeout',
    'station_screensaver': 'Screen Saver',
    'station_volume': 'Station Volume',
    'transparent_noise_cancelling_level': 'Transparency',
    'volume_limiter': 'Volume Limiter',
    'wireless_mode': 'Wireless Mode',
    'wireless_pairing': 'Wireless Pairing',
}

DEVICE_CAPABILITY_GROUPS = (
    {
        'key': 'microphone',
        'title': 'Microphone',
        'settings': (
            'mic_volume',
            'mic_side_tone',
            'sidetone',
            'mic_sidetone_boom',
            'mic_sidetone_ear',
            'mic_led_brightness',
            'mic_mute_led_brightness',
        ),
        'fallback': 'Mic volume and sidetone controls appear when exposed by the connected headset.',
    },
    {
        'key': 'noise_control',
        'title': 'Noise Control',
        'settings': (
            'noise_cancelling',
            'noise_cancelling_level',
            'transparent_noise_cancelling_level',
        ),
        'fallback': 'ANC and transparency controls appear only on supported headset models.',
    },
    {
        'key': 'power_wireless',
        'title': 'Power & Wireless',
        'settings': (
            'pm_shutdown',
            'auto_off_time_minutes',
            'wireless_mode',
            'wireless_pairing',
            'bluetooth_powerup_state',
            'bluetooth_power_status',
            'bluetooth_default',
            'bluetooth_auto_mute',
        ),
        'fallback': 'Power, Bluetooth, and wireless controls depend on device metadata.',
    },
    {
        'key': 'audio_dac',
        'title': 'Audio & DAC',
        'settings': (
            'station_volume',
            'gain',
            'line_out',
            'volume_limiter',
            'station_screen_brightness',
            'station_screen_saver_timeout',
            'station_screensaver',
            'station_home_screen_view',
            'station_home_screen_options',
        ),
        'fallback': 'GameDAC, limiter, and display controls appear when mapped for the device.',
    },
)

DEVICE_CONTROL_SNAPSHOT_GROUPS = (
    {
        'key': 'microphone',
        'title': 'Microphone Levels',
        'settings': (
            'mic_volume',
            'mic_side_tone',
            'sidetone',
            'mic_sidetone_boom',
            'mic_sidetone_ear',
        ),
        'fallback': 'Mic level and sidetone values appear when the device exposes them.',
    },
    {
        'key': 'noise_control',
        'title': 'Noise Control',
        'settings': (
            'noise_cancelling',
            'noise_cancelling_level',
            'transparent_noise_cancelling_level',
        ),
        'fallback': 'ANC and transparency values appear on supported models.',
    },
    {
        'key': 'power_wireless',
        'title': 'Power & Wireless',
        'settings': (
            'wireless_mode',
            'auto_off_time_minutes',
            'pm_shutdown',
            'bluetooth_power_status',
            'bluetooth_default',
            'bluetooth_auto_mute',
        ),
        'fallback': 'Power, wireless, and Bluetooth values depend on device metadata.',
    },
    {
        'key': 'audio_dac',
        'title': 'DAC / Output',
        'settings': (
            'station_volume',
            'gain',
            'line_out',
            'volume_limiter',
        ),
        'fallback': 'GameDAC and output values appear when mapped for this device.',
    },
)


def flatten_status_values(status: StatusPayload | dict) -> dict[str, str | int]:
    values: dict[str, str | int] = {}
    for status_obj in status.values():
        if not isinstance(status_obj, dict):
            continue
        for name, payload in status_obj.items():
            if isinstance(payload, dict) and 'value' in payload:
                values[name] = payload['value']

    return values


def safe_percentage(value: str | int | None, fallback: int = 100) -> int:
    if isinstance(value, int):
        return max(0, min(100, value))

    try:
        return max(0, min(100, int(value))) if value is not None else fallback
    except ValueError:
        return fallback


def first_status_value(values: dict[str, str | int], keys: list[str], fallback: str) -> str:
    for key in keys:
        if key not in values:
            continue

        value = values[key]
        return f'{value}%' if key.endswith('battery_charge') and isinstance(value, int) else str(value)

    return fallback


def output_endpoint_summary() -> str:
    return ' / '.join(endpoint.label for endpoint in VIRTUAL_AUDIO_ENDPOINTS if endpoint.kind == 'sink' and endpoint.implemented)


def ready_output_endpoint_summary(settings: dict) -> str:
    endpoint_states = settings.get('audio_endpoints', [])
    if not isinstance(endpoint_states, list) or not endpoint_states:
        return output_endpoint_summary()

    ready_labels = [
        str(endpoint.get('label') or endpoint.get('node_name'))
        for endpoint in endpoint_states
        if isinstance(endpoint, dict)
        and endpoint.get('kind') == 'sink'
        and endpoint.get('implemented') is True
        and endpoint.get('present') is True
    ]

    if ready_labels:
        return f"{len(ready_labels)} ready: {' / '.join(ready_labels)}"

    return 'No virtual outputs ready'


def output_endpoint_readiness_detail(settings: dict) -> str:
    endpoint_states = settings.get('audio_endpoints', [])
    if not isinstance(endpoint_states, list) or not endpoint_states:
        planned_labels = [endpoint.label for endpoint in VIRTUAL_AUDIO_ENDPOINTS if not endpoint.implemented]
        detail = f'Catalog: {output_endpoint_summary()}'
        if planned_labels:
            detail = f"{detail} | Planned: {' / '.join(planned_labels)}"
        return detail

    ready_labels = []
    missing_labels = []
    planned_labels = []
    for endpoint in endpoint_states:
        if not isinstance(endpoint, dict):
            continue

        label = str(endpoint.get('label') or endpoint.get('node_name') or 'Unknown')
        if endpoint.get('implemented') is not True:
            planned_labels.append(label)
        elif endpoint.get('kind') == 'sink' and endpoint.get('present') is True:
            ready_labels.append(label)
        elif endpoint.get('kind') == 'sink':
            missing_labels.append(label)

    details = []
    if ready_labels:
        details.append(f"Ready: {' / '.join(ready_labels)}")
    if missing_labels:
        details.append(f"Missing: {' / '.join(missing_labels)}")
    if planned_labels:
        details.append(f"Planned: {' / '.join(planned_labels)}")

    return ' | '.join(details) if details else 'No virtual endpoint metadata reported.'


def routing_overview_summary(settings: dict) -> dict[str, str]:
    endpoint_states = settings.get('audio_endpoints', [])
    routes = settings.get('application_routes', [])
    if not isinstance(endpoint_states, list):
        endpoint_states = []
    if not isinstance(routes, list):
        routes = []

    implemented_outputs = [
        endpoint
        for endpoint in endpoint_states
        if isinstance(endpoint, dict)
        and endpoint.get('kind') == 'sink'
        and endpoint.get('implemented') is True
    ]
    ready_outputs = [
        endpoint
        for endpoint in implemented_outputs
        if endpoint.get('present') is True
    ]
    missing_outputs = [
        endpoint
        for endpoint in implemented_outputs
        if endpoint.get('present') is not True
    ]

    if implemented_outputs:
        outputs_value = f'{len(ready_outputs)} ready / {len(missing_outputs)} missing'
        ready_labels = [str(endpoint.get('label') or endpoint.get('node_name')) for endpoint in ready_outputs]
        outputs_detail = f"Ready: {' / '.join(ready_labels)}" if ready_labels else 'No virtual outputs are ready yet.'
    elif endpoint_states:
        outputs_value = 'No outputs reported'
        outputs_detail = 'The service returned endpoint metadata, but no implemented virtual outputs.'
    else:
        outputs_value = 'Waiting'
        outputs_detail = f'Catalog: {output_endpoint_summary()}'

    active_routes = [
        route
        for route in routes
        if isinstance(route, dict) and isinstance(route.get('stream_index'), int)
    ]
    if active_routes:
        route_count = len(active_routes)
        routes_value = f'{route_count} active stream' if route_count == 1 else f'{route_count} active streams'
        route_labels = []
        for route in active_routes[:3]:
            app_name = route.get('application_name') or route.get('name') or 'Unknown app'
            current = route.get('current_endpoint_label') or route.get('sink_description') or route.get('sink_node_name') or 'current output'
            route_labels.append(f'{app_name} -> {current}')
        routes_detail = f"Streams: {' / '.join(route_labels)}"
        overflow = route_count - len(route_labels)
        if overflow:
            routes_detail = f'{routes_detail} / +{overflow} more'
    else:
        routes_value = 'No active streams'
        routes_detail = 'Open audio apps will appear here when PulseAudio/PipeWire-pulse reports active playback streams.'

    planned_labels = [endpoint.label for endpoint in VIRTUAL_AUDIO_ENDPOINTS if not endpoint.implemented]
    planned_count = len(planned_labels)
    planned_value = f'{planned_count} planned endpoint' if planned_count == 1 else f'{planned_count} planned endpoints'
    planned_detail = (
        f"Planned: {' / '.join(planned_labels)} source plus persistent app/game routing rules."
        if planned_labels
        else 'Persistent app/game routing rules are planned for future native PipeWire/WirePlumber work.'
    )

    return {
        'outputs_value': outputs_value,
        'outputs_detail': outputs_detail,
        'apps_value': routes_value,
        'apps_detail': routes_detail,
        'planned_value': planned_value,
        'planned_detail': planned_detail,
    }


def application_route_rows(settings: dict) -> list[dict[str, str | int]]:
    routes = settings.get('application_routes', [])
    if not isinstance(routes, list):
        return []

    rows: list[dict[str, str | int]] = []
    for route in routes:
        if not isinstance(route, dict) or not isinstance(route.get('stream_index'), int):
            continue

        stream_index = route['stream_index']
        app_name = route.get('application_name') or route.get('name') or 'Unknown app'
        current = route.get('current_endpoint_label') or route.get('sink_description') or route.get('sink_node_name') or 'current output'

        details = []
        process = route.get('process_binary')
        process_id = route.get('process_id')
        if process:
            details.append(str(process))
        if process_id:
            details.append(f'PID {process_id}')
        details.append(f'Stream {stream_index}')

        rows.append({
            'stream_index': stream_index,
            'title': str(app_name),
            'current': str(current),
            'detail': ' | '.join(details),
        })

    return rows


def endpoint_route_map(settings: dict) -> list[dict[str, str]]:
    endpoint_states = settings.get('audio_endpoints', [])
    if not isinstance(endpoint_states, list):
        endpoint_states = []

    states_by_node = {
        state.get('node_name'): state
        for state in endpoint_states
        if isinstance(state, dict) and isinstance(state.get('node_name'), str)
    }

    route_rows = application_route_rows(settings)
    raw_routes = settings.get('application_routes', [])
    if not isinstance(raw_routes, list):
        raw_routes = []

    rows_by_stream = {
        route['stream_index']: route
        for route in route_rows
        if isinstance(route.get('stream_index'), int)
    }
    apps_by_endpoint: dict[str, list[str]] = {}
    for raw_route in raw_routes:
        if not isinstance(raw_route, dict) or not isinstance(raw_route.get('stream_index'), int):
            continue

        endpoint_node = raw_route.get('current_endpoint_node_name') or raw_route.get('sink_node_name')
        if not isinstance(endpoint_node, str) or not endpoint_node:
            label = raw_route.get('current_endpoint_label')
            endpoint_node = next(
                (
                    endpoint.node_name
                    for endpoint in VIRTUAL_AUDIO_ENDPOINTS
                    if isinstance(label, str) and label == endpoint.label
                ),
                '',
            )
        if not endpoint_node:
            continue

        route = rows_by_stream.get(raw_route['stream_index'])
        title = str(route['title']) if route else str(raw_route.get('application_name') or raw_route.get('name') or 'Unknown app')
        apps_by_endpoint.setdefault(endpoint_node, []).append(title)

    result = []
    for endpoint in VIRTUAL_AUDIO_ENDPOINTS:
        state = states_by_node.get(endpoint.node_name, {})
        label = str(state.get('label') or endpoint.label) if isinstance(state, dict) else endpoint.label
        apps = apps_by_endpoint.get(endpoint.node_name, [])

        if not endpoint.implemented:
            value = 'Planned'
            detail = 'Microphone source routing is planned; app routing applies to playback outputs today.'
        elif apps:
            count = len(apps)
            value = f'{count} active app' if count == 1 else f'{count} active apps'
            visible = apps[:3]
            overflow = count - len(visible)
            detail = f"Assigned: {' / '.join(visible)}"
            if overflow:
                detail = f'{detail} / +{overflow} more'
        elif isinstance(state, dict) and state.get('present') is True:
            value = 'Ready'
            detail = 'No active app streams are assigned to this output yet.'
        elif endpoint_states:
            value = 'Missing'
            detail = 'Virtual output is not available yet.'
        else:
            value = 'Waiting'
            detail = 'Waiting for endpoint state and active app streams.'

        result.append({
            'key': endpoint.node_name,
            'title': label,
            'state': value,
            'detail': detail,
        })

    return result


def profile_app_context_summary(settings: dict) -> dict[str, str]:
    route_rows = application_route_rows(settings)
    if not route_rows:
        return {
            'value': 'No active streams',
            'detail': 'Open audio apps will appear here before app/game profile switching is implemented.',
        }

    count = len(route_rows)
    value = f'{count} active app' if count == 1 else f'{count} active apps'
    visible = [
        f"{route['title']} -> {route['current']}"
        for route in route_rows[:3]
    ]
    overflow = count - len(visible)
    detail = f"Context: {' / '.join(visible)}"
    if overflow:
        detail = f'{detail} / +{overflow} more'

    return {
        'value': value,
        'detail': detail,
    }


def active_profile_name(settings: dict) -> str:
    profiles = settings.get('profiles', {})
    if not isinstance(profiles, dict):
        return 'Default'

    active = profiles.get('active', 'Default')

    return active if isinstance(active, str) and active else 'Default'


def available_profile_names(settings: dict) -> list[str]:
    profiles = settings.get('profiles', {})
    if not isinstance(profiles, dict):
        return []

    available = profiles.get('available', [])
    if not isinstance(available, list):
        return []

    return [profile for profile in available if isinstance(profile, str) and profile]


def profile_workflow_summary(settings: dict) -> dict[str, str]:
    available = available_profile_names(settings)
    count = len(available)
    if count == 0:
        saved_value = 'No saved profiles'
        saved_detail = 'Save the current device settings to start a per-device profile list.'
    else:
        saved_value = f'{count} saved profile' if count == 1 else f'{count} saved profiles'
        visible = available[:4]
        overflow = count - len(visible)
        saved_detail = f"Available: {' / '.join(visible)}"
        if overflow:
            saved_detail = f'{saved_detail} / +{overflow} more'

    has_device_settings = isinstance(settings.get('device'), dict) and bool(settings.get('device'))
    save_value = 'Ready' if has_device_settings else 'No device'
    save_detail = (
        'Save captures the currently exposed device settings for this headset.'
        if has_device_settings
        else 'Connect a supported headset before saving a profile.'
    )

    return {
        'saved_value': saved_value,
        'saved_detail': saved_detail,
        'save_value': save_value,
        'save_detail': save_detail,
        'automation_value': 'Planned',
        'automation_detail': 'Future app/game switching will build on active app routes and profile metadata.',
    }


def connected_device_name(settings: dict, fallback: str = 'No device detected') -> str:
    device_info = settings.get('device_info', {})
    if not isinstance(device_info, dict):
        return fallback

    name = device_info.get('name')
    return name if isinstance(name, str) and name else fallback


def connected_device_detail(settings: dict) -> str:
    device_info = settings.get('device_info', {})
    if not isinstance(device_info, dict):
        return 'Waiting for matched USB/HID metadata.'

    vendor_id = device_info.get('vendor_id')
    product_id = device_info.get('product_id')
    if isinstance(vendor_id, str) and vendor_id and isinstance(product_id, str) and product_id:
        return f'USB {vendor_id}:{product_id}'

    if isinstance(device_info.get('name'), str) and device_info.get('name'):
        return 'Matched headset or DAC metadata.'

    return 'Waiting for matched USB/HID metadata.'


def battery_status_detail(status: StatusPayload | dict) -> str:
    values = flatten_status_values(status)
    power_state = first_status_value(values, ['headset_power_status', 'bluetooth_power_status'], '')
    if power_state:
        return f'Power state: {power_state}'
    if status:
        return 'Battery metadata received without a power state.'
    return 'Waiting for headset battery status.'


def microphone_status_detail(status: StatusPayload | dict) -> str:
    values = flatten_status_values(status)
    if 'mic_status' in values:
        return f"Mute state: {values['mic_status']}"
    if 'mic_volume' in values:
        return f"Volume status: {values['mic_volume']}"
    return 'Waiting for microphone status.'


def active_profile_detail(settings: dict) -> str:
    available = available_profile_names(settings)
    if not available:
        return 'Save a profile after device settings load.'

    visible = available[:3]
    overflow = len(available) - len(visible)
    detail = f"Saved: {' / '.join(visible)}"
    if overflow:
        detail = f'{detail} / +{overflow} more'
    return detail


def dashboard_settings_summary(settings: dict) -> dict[str, str]:
    summary = {
        'outputs': ready_output_endpoint_summary(settings),
        'profile': active_profile_name(settings),
    }

    device_name = connected_device_name(settings, '')
    if device_name:
        summary['device'] = device_name

    return summary


def dashboard_detail_summary(status: StatusPayload | dict, settings: dict | None = None) -> dict[str, str]:
    settings = settings or {}
    return {
        'device': connected_device_detail(settings),
        'battery': battery_status_detail(status),
        'microphone': microphone_status_detail(status),
        'outputs': output_endpoint_readiness_detail(settings),
        'profile': active_profile_detail(settings),
    }


def dashboard_summary(status: StatusPayload | dict, settings: dict | None = None) -> dict[str, str]:
    values = flatten_status_values(status)
    online_state = first_status_value(values, ['headset_power_status', 'bluetooth_power_status'], 'Connected' if status else 'No device detected')
    mic_state = first_status_value(values, ['mic_status', 'mic_volume'], 'Unknown')

    return {
        'device': connected_device_name(settings or {}, online_state),
        'battery': first_status_value(values, ['headset_battery_charge', 'charge_slot_battery_charge'], 'Unknown'),
        'microphone': mic_state,
    }


def header_context_summary(status: StatusPayload | dict, settings: dict | None = None) -> dict[str, str]:
    summary = dashboard_summary(status, settings)
    settings = settings or {}
    return {
        'device': summary['device'],
        'battery': summary['battery'],
        'profile': active_profile_name(settings),
        'outputs': ready_output_endpoint_summary(settings),
    }


def _friendly_setting_names(setting_names: list[str]) -> str:
    return ' / '.join(DEVICE_SETTING_LABELS.get(name, name.replace('_', ' ').title()) for name in setting_names)


def _friendly_setting_value(name: str, value: str | int | bool, settings_config: dict) -> str:
    config = settings_config.get(name, {})
    if not isinstance(config, dict):
        config = {}

    values_mapping = config.get('values_mapping', {})
    if isinstance(values_mapping, dict):
        mapped = values_mapping.get(str(value))
        if mapped is not None:
            return str(mapped).replace('_', ' ').title()

    if isinstance(value, bool):
        return 'On' if value else 'Off'
    if name.endswith('_minutes') and isinstance(value, int):
        return f'{value} min'
    if ('volume' in name or name.endswith('_level')) and isinstance(value, int):
        return f'{value}%'

    return str(value)


def _friendly_setting_pairs(setting_names: list[str], device_settings: dict, settings_config: dict) -> str:
    pairs = []
    for name in setting_names:
        if name not in device_settings:
            continue

        label = DEVICE_SETTING_LABELS.get(name, name.replace('_', ' ').title())
        value = _friendly_setting_value(name, device_settings[name], settings_config)
        pairs.append(f'{label}: {value}')

    return ' / '.join(pairs)


def device_capability_summary(settings: dict) -> list[dict[str, str]]:
    device_settings = settings.get('device', {})
    settings_config = settings.get('settings_config', {})
    if not isinstance(device_settings, dict):
        device_settings = {}
    if not isinstance(settings_config, dict):
        settings_config = {}

    has_device = bool(device_settings)
    summaries = []
    for group in DEVICE_CAPABILITY_GROUPS:
        group_settings = list(group['settings'])
        active_controls = [name for name in group_settings if name in device_settings]
        configured_controls = [name for name in group_settings if name in settings_config]
        controls = active_controls or configured_controls

        if controls:
            state = 'Supported'
            detail = f"Controls: {_friendly_setting_names(controls)}"
        elif has_device:
            state = 'Not exposed'
            detail = str(group['fallback'])
        else:
            state = 'No device'
            detail = 'Connect a supported headset to show available hardware controls.'

        summaries.append({
            'key': str(group['key']),
            'title': str(group['title']),
            'state': state,
            'detail': detail,
        })

    return summaries


def device_control_snapshot(settings: dict) -> list[dict[str, str]]:
    device_settings = settings.get('device', {})
    settings_config = settings.get('settings_config', {})
    if not isinstance(device_settings, dict):
        device_settings = {}
    if not isinstance(settings_config, dict):
        settings_config = {}

    has_device = bool(device_settings)
    snapshots = []
    for group in DEVICE_CONTROL_SNAPSHOT_GROUPS:
        group_settings = list(group['settings'])
        active_settings = [name for name in group_settings if name in device_settings]

        if active_settings:
            state = 'Ready'
            detail = _friendly_setting_pairs(active_settings, device_settings, settings_config)
        elif has_device:
            state = 'Not exposed'
            detail = str(group['fallback'])
        else:
            state = 'No device'
            detail = 'Connect a supported headset to show current hardware values.'

        snapshots.append({
            'key': str(group['key']),
            'title': str(group['title']),
            'state': state,
            'detail': detail,
        })

    return snapshots


def mixer_levels(status: StatusPayload | dict) -> dict[str, int]:
    values = flatten_status_values(status)
    media_mix = safe_percentage(values.get('media_mix'), 100)
    chat_mix = safe_percentage(values.get('chat_mix'), 100)

    result: dict[str, int] = {}
    for endpoint in VIRTUAL_AUDIO_ENDPOINTS:
        if not endpoint.implemented:
            result[endpoint.node_name] = 0
        elif endpoint.mix_group == 'chat':
            result[endpoint.node_name] = chat_mix
        elif endpoint.mix_group == 'media':
            result[endpoint.node_name] = media_mix

    return result


def mixer_overview_summary(settings: dict) -> dict[str, str]:
    endpoint_states = settings.get('audio_endpoints', [])
    if not isinstance(endpoint_states, list):
        endpoint_states = []

    states_by_node = {
        state.get('node_name'): state
        for state in endpoint_states
        if isinstance(state, dict) and isinstance(state.get('node_name'), str)
    }

    ready_labels = []
    missing_labels = []
    planned_labels = []
    for endpoint in VIRTUAL_AUDIO_ENDPOINTS:
        state = states_by_node.get(endpoint.node_name, {})
        label = str(state.get('label') or endpoint.label) if isinstance(state, dict) else endpoint.label
        implemented = endpoint.implemented
        if isinstance(state, dict) and 'implemented' in state:
            implemented = state.get('implemented') is True

        if not implemented:
            planned_labels.append(label)
        elif isinstance(state, dict) and state.get('present') is True:
            ready_labels.append(label)
        elif endpoint_states:
            missing_labels.append(label)

    if endpoint_states:
        channel_value = f'{len(ready_labels)} ready / {len(missing_labels)} missing / {len(planned_labels)} planned'
        detail_parts = []
        if ready_labels:
            detail_parts.append(f"Ready: {' / '.join(ready_labels)}")
        if missing_labels:
            detail_parts.append(f"Missing: {' / '.join(missing_labels)}")
        if planned_labels:
            detail_parts.append(f"Planned: {' / '.join(planned_labels)}")
        channel_detail = ' | '.join(detail_parts) if detail_parts else 'No endpoint state reported.'
    else:
        channel_value = 'Waiting'
        channel_detail = output_endpoint_readiness_detail(settings)

    media_labels = [
        endpoint.label
        for endpoint in VIRTUAL_AUDIO_ENDPOINTS
        if endpoint.kind == 'sink' and endpoint.mix_group == 'media'
    ]
    chat_labels = [
        endpoint.label
        for endpoint in VIRTUAL_AUDIO_ENDPOINTS
        if endpoint.kind == 'sink' and endpoint.mix_group == 'chat'
    ]

    return {
        'channels_value': channel_value,
        'channels_detail': channel_detail,
        'media_value': ' / '.join(media_labels),
        'media_detail': 'Media mix drives Game, Media, and Aux channels.',
        'chat_value': ' / '.join(chat_labels),
        'chat_detail': 'Chat mix drives voice chat separately when the headset reports ChatMix.',
    }


def chatmix_balance_summary(status: StatusPayload | dict) -> dict[str, str | int]:
    values = flatten_status_values(status)
    has_media_mix = 'media_mix' in values
    has_chat_mix = 'chat_mix' in values
    media_mix = safe_percentage(values.get('media_mix'), 100)
    chat_mix = safe_percentage(values.get('chat_mix'), 100)

    if not has_media_mix and not has_chat_mix:
        return {
            'value': 'Waiting',
            'detail': 'Waiting for media_mix and chat_mix status values from the headset or GameDAC.',
            'media_level': media_mix,
            'chat_level': chat_mix,
        }

    if has_media_mix and has_chat_mix:
        detail = 'Game, Media, and Aux follow media mix; Chat follows chat mix.'
    elif has_media_mix:
        detail = 'Chat mix is not reported yet; Chat is shown at the default level.'
    else:
        detail = 'Media mix is not reported yet; Game, Media, and Aux are shown at the default level.'

    return {
        'value': f'Game/Media/Aux {media_mix}% / Chat {chat_mix}%',
        'detail': detail,
        'media_level': media_mix,
        'chat_level': chat_mix,
    }


def dashboard_control_surface_summary(status: StatusPayload | dict, settings: dict | None = None) -> list[dict[str, str]]:
    settings = settings or {}
    balance = chatmix_balance_summary(status)
    if balance['value'] == 'Waiting':
        mix_state = 'Waiting'
        mix_detail = str(balance['detail'])
    else:
        mix_state = 'Ready'
        mix_detail = f"{balance['value']}. {balance['detail']}"

    routing = routing_overview_summary(settings)
    capabilities = device_capability_summary(settings)
    supported_capabilities = [
        capability['title']
        for capability in capabilities
        if capability['state'] == 'Supported'
    ]
    if supported_capabilities:
        control_count = len(supported_capabilities)
        control_state = f'{control_count} supported area' if control_count == 1 else f'{control_count} supported areas'
        control_detail = f"Available: {' / '.join(supported_capabilities)}"
    elif any(capability['state'] == 'Not exposed' for capability in capabilities):
        control_state = 'Not exposed'
        control_detail = 'This headset is connected, but no mapped control groups are exposed yet.'
    else:
        control_state = 'No device'
        control_detail = 'Connect a supported headset to expose device controls.'

    return [
        {
            'key': 'mix',
            'title': 'ChatMix',
            'state': mix_state,
            'detail': mix_detail,
        },
        {
            'key': 'routes',
            'title': 'App Routes',
            'state': routing['apps_value'],
            'detail': routing['apps_detail'],
        },
        {
            'key': 'controls',
            'title': 'Device Controls',
            'state': control_state,
            'detail': control_detail,
        },
    ]


def demo_status() -> StatusPayload:
    return {
        'headset': {
            'headset_power_status': {'value': 'online', 'type': 'label'},
            'headset_battery_charge': {'value': 87, 'type': 'percentage'},
        },
        'mic': {
            'mic_status': {'value': 'unmuted', 'type': 'label'},
        },
        'gamedac': {
            'media_mix': {'value': 70, 'type': 'percentage'},
            'chat_mix': {'value': 55, 'type': 'percentage'},
        },
    }


def demo_settings() -> dict:
    endpoint_descriptions = {
        'Arctis_Game': ('Demo Game', True, True),
        'Arctis_Chat': ('Demo Chat', True, False),
        'Arctis_Media': ('Demo Media', True, False),
        'Arctis_Aux': ('Demo Aux', False, False),
        'Arctis_Microphone': ('Demo Microphone', False, False),
    }

    return {
        'general': {},
        'device': {
            'mic_volume': 82,
            'mic_side_tone': 2,
            'noise_cancelling': 1,
            'transparent_noise_cancelling_level': 4,
            'wireless_mode': 0,
            'auto_off_time_minutes': 30,
            'station_volume': 60,
            'gain': 1,
        },
        'device_info': {
            'name': 'Arctis Nova 7 Wireless (demo)',
            'vendor_id': '1038',
            'product_id': '2202',
        },
        'profiles': {
            'available': ['Default', 'Late Night', 'Footsteps'],
            'active': 'Late Night',
        },
        'audio_endpoints': [
            {
                'node_name': endpoint.node_name,
                'label': endpoint.label,
                'kind': endpoint.kind,
                'mix_group': endpoint.mix_group,
                'implemented': endpoint.implemented,
                'present': endpoint_descriptions[endpoint.node_name][1],
                'default': endpoint_descriptions[endpoint.node_name][2],
                'description': endpoint_descriptions[endpoint.node_name][0],
            }
            for endpoint in VIRTUAL_AUDIO_ENDPOINTS
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
                'sink_description': 'Demo Game',
                'current_endpoint_node_name': 'Arctis_Game',
                'current_endpoint_label': 'Game',
                'routable': True,
            },
            {
                'stream_index': 56,
                'name': 'Discord',
                'application_name': 'Discord',
                'process_binary': 'Discord',
                'process_id': '5678',
                'sink_index': 2,
                'sink_node_name': 'Arctis_Chat',
                'sink_description': 'Demo Chat',
                'current_endpoint_node_name': 'Arctis_Chat',
                'current_endpoint_label': 'Chat',
                'routable': True,
            },
        ],
        'settings_config': {},
    }
