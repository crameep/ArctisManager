from pathlib import Path
from typing import Any, Mapping

from ruamel.yaml import YAML

from linux_arctis_manager.constants import PROFILES_FOLDER

ProfileValue = bool | int | str | None


def normalize_profile_name(name: str) -> str:
    normalized = name.strip()

    if not normalized:
        raise ValueError('Profile name cannot be empty')
    if '\n' in normalized or '\r' in normalized:
        raise ValueError('Profile name cannot contain line breaks')
    if len(normalized) > 80:
        raise ValueError('Profile name cannot be longer than 80 characters')

    return normalized


class DeviceProfileStore:
    def __init__(self, vendor_id: int, product_id: int, profiles_folder: Path = PROFILES_FOLDER):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.profiles_folder = profiles_folder

    def _profiles_file(self) -> Path:
        return self.profiles_folder / f'{self.vendor_id:04x}_{self.product_id:04x}.yaml'

    def _read_raw(self) -> dict[str, Any]:
        profiles_file = self._profiles_file()

        if not profiles_file.exists():
            return {'active_profile': 'Default', 'profiles': {}}

        yaml = YAML(typ='safe')
        raw = yaml.load(profiles_file) or {}

        profiles = raw.get('profiles', {})
        if not isinstance(profiles, dict):
            profiles = {}

        cleaned_profiles: dict[str, dict[str, ProfileValue]] = {}
        for profile_name, settings in profiles.items():
            if not isinstance(profile_name, str) or not isinstance(settings, dict):
                continue

            cleaned_profiles[profile_name] = {
                str(setting_name): value
                for setting_name, value in settings.items()
                if isinstance(value, (bool, int, str)) or value is None
            }

        active_profile = raw.get('active_profile', 'Default')
        if not isinstance(active_profile, str) or active_profile not in cleaned_profiles:
            active_profile = 'Default'

        return {'active_profile': active_profile, 'profiles': cleaned_profiles}

    def _write_raw(self, raw: dict[str, Any]) -> None:
        profiles_file = self._profiles_file()
        profiles_file.parent.mkdir(parents=True, exist_ok=True)

        yaml = YAML(typ='safe')
        yaml.dump(raw, profiles_file)

    def list_profiles(self) -> list[str]:
        return sorted(self._read_raw()['profiles'].keys())

    def active_profile(self) -> str:
        return self._read_raw()['active_profile']

    def metadata(self) -> dict[str, str | list[str]]:
        return {
            'available': self.list_profiles(),
            'active': self.active_profile(),
        }

    def save_profile(self, name: str, settings: Mapping[str, ProfileValue]) -> str:
        profile_name = normalize_profile_name(name)
        raw = self._read_raw()

        raw['profiles'][profile_name] = {
            str(setting_name): value
            for setting_name, value in settings.items()
            if isinstance(value, (bool, int, str)) or value is None
        }
        raw['active_profile'] = profile_name
        self._write_raw(raw)

        return profile_name

    def get_profile(self, name: str) -> dict[str, ProfileValue] | None:
        profile_name = normalize_profile_name(name)
        profile = self._read_raw()['profiles'].get(profile_name)

        return dict(profile) if isinstance(profile, dict) else None

    def set_active_profile(self, name: str) -> None:
        profile_name = normalize_profile_name(name)
        raw = self._read_raw()

        if profile_name not in raw['profiles']:
            raise KeyError(profile_name)

        raw['active_profile'] = profile_name
        self._write_raw(raw)
