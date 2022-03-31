import json

SETTINGS_FILE_NAME = 'settings.json'
AUTO_CONNECT_ON_STARTUP_VPN_NAMES_KEY = 'auto_connect_on_startup_vpn_names'
LAUNCH_APP_ON_STARTUP_KEY = 'launch_app_on_startup'


def read_settings(key):
    with open(SETTINGS_FILE_NAME) as settings:
        data = json.load(settings)
    return data[key]


def write_settings(auto_connect_on_startup_vpn_names, launch_app_on_startup):
    with open(SETTINGS_FILE_NAME, 'w') as settings:
        json.dump({
            AUTO_CONNECT_ON_STARTUP_VPN_NAMES_KEY: auto_connect_on_startup_vpn_names,
            LAUNCH_APP_ON_STARTUP_KEY: launch_app_on_startup
        }, settings)


def read_auto_connect_on_startup_vpn_names():
    return read_settings(AUTO_CONNECT_ON_STARTUP_VPN_NAMES_KEY)


def read_launch_app_on_startup():
    return read_settings(LAUNCH_APP_ON_STARTUP_KEY)


def write_auto_connect_on_startup_vpn_names(auto_connect_on_startup_vpn_names):
    write_settings(auto_connect_on_startup_vpn_names, read_launch_app_on_startup())


def write_launch_app_on_startup(launch_app_on_startup):
    write_settings(read_auto_connect_on_startup_vpn_names(), launch_app_on_startup)
