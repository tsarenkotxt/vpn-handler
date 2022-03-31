from setuptools import setup

APP = ['vpn_handler.py']
APP_NAME = "VPN Handler (arm)"
DATA_FILES = ['settings.json']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',
    'packages': ['rumps'],
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleVersion': "0.1.0",
        'CFBundleShortVersionString': "0.1.0",
        'LSUIElement': True
    }
}

setup(
    app=APP,
    name=APP_NAME,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=['rumps == 0.3.0']
)
