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


def _friendly_setting_names(setting_names: list[str]) -> str:
    return ' / '.join(DEVICE_SETTING_LABELS.get(name, name.replace('_', ' ').title()) for name in setting_names)


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
