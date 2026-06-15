from linux_arctis_manager.audio_endpoints import VIRTUAL_AUDIO_ENDPOINTS

StatusPayload = dict[str, dict[str, dict[str, str | int]]]


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


def active_profile_name(settings: dict) -> str:
    profiles = settings.get('profiles', {})
    if not isinstance(profiles, dict):
        return 'Default'

    active = profiles.get('active', 'Default')

    return active if isinstance(active, str) and active else 'Default'


def dashboard_settings_summary(settings: dict) -> dict[str, str]:
    return {
        'outputs': ready_output_endpoint_summary(settings),
        'profile': active_profile_name(settings),
    }


def dashboard_summary(status: StatusPayload | dict) -> dict[str, str]:
    values = flatten_status_values(status)
    online_state = first_status_value(values, ['headset_power_status', 'bluetooth_power_status'], 'Connected' if status else 'No device detected')
    mic_state = first_status_value(values, ['mic_status', 'mic_volume'], 'Unknown')

    return {
        'device': online_state,
        'battery': first_status_value(values, ['headset_battery_charge', 'charge_slot_battery_charge'], 'Unknown'),
        'microphone': mic_state,
    }


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
