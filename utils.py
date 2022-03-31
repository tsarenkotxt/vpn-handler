import os
import time

import properties

try:
    import httplib  # python < 3.0
except:
    import http.client as httplib

MACOS_APP_SUFFIX = '.app'


def execute_cmd(cmd):
    stream = os.popen(cmd)
    try:
        return stream.read()
    finally:
        stream.close()


def enable_launch_app_on_startup(app_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if MACOS_APP_SUFFIX in current_dir:
        app_path = current_dir[0:current_dir.index(MACOS_APP_SUFFIX) + len(MACOS_APP_SUFFIX)]
        os.system("""
                  osascript -e 'tell application "System Events" \
                    to make login item at end with properties {{name: "{}", path:"{}", hidden:false}}'
                  """.format(app_name + MACOS_APP_SUFFIX, app_path))


def disable_launch_app_on_startup(app_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if MACOS_APP_SUFFIX in current_dir:
        os.system("""
                  osascript -e 'tell application "System Events" to delete login item "{}"'
                  """.format(app_name))


def display_notification(title, text):
    os.system("""
              osascript -e 'display notification "{}" with title "{}"'
              """.format(text, title))


def get_active_user():
    output = execute_cmd("stat -f '%Su' /dev/console")
    return output[:len(output) - 1]


def is_user_active(user):
    return user == get_active_user()


def wait_until_condition(condition, retry_attempts, backoff):
    for attempt in range(retry_attempts):
        if condition():
            return True
        else:
            time.sleep((attempt + 1) * backoff)
    else:
        return condition()


def is_internet_connected():
    connection = httplib.HTTPSConnection('google.com', 443,
                                         timeout=properties.INTERNET_VERIFICATION_TIMEOUT)
    try:
        connection.request('GET', '/')
        return True
    except Exception:
        return False
    finally:
        connection.close()
