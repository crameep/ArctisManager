import pytest

from linux_arctis_manager.profiles import DeviceProfileStore, normalize_profile_name


def test_device_profile_store_saves_lists_and_loads_settings(tmp_path):
    store = DeviceProfileStore(0x1038, 0x2202, tmp_path)

    saved_name = store.save_profile('  Movies  ', {
        'sidetone': 4,
        'mic_volume': 72,
    })

    assert saved_name == 'Movies'
    assert store.list_profiles() == ['Movies']
    assert store.active_profile() == 'Movies'
    assert store.metadata() == {'available': ['Movies'], 'active': 'Movies'}
    assert store.get_profile('Movies') == {
        'sidetone': 4,
        'mic_volume': 72,
    }


def test_device_profile_store_tracks_active_profile(tmp_path):
    store = DeviceProfileStore(0x1038, 0x2202, tmp_path)

    store.save_profile('Default', {'sidetone': 2})
    store.save_profile('Late Night', {'sidetone': 1})
    store.set_active_profile('Default')

    assert store.list_profiles() == ['Default', 'Late Night']
    assert store.active_profile() == 'Default'


@pytest.mark.parametrize('name', ['', '   ', 'bad\nname', 'x' * 81])
def test_profile_names_reject_empty_line_breaks_and_overlong_values(name):
    with pytest.raises(ValueError):
        normalize_profile_name(name)
