# -*- coding: utf-8 -*-

import threading
import time

import properties
import utils

VPN_CONNECTED_STATUS = 'connected\n'
VPN_DISCONNECTED_STATUS = 'disconnected\n'


def get_vpn_names():
    output = utils.execute_cmd('scutil --nc list')
    output_lines = output.split('\n')
    vpn_names = list()

    if len(output_lines) <= 2:
        return vpn_names

    for index in range(1, len(output_lines) - 1):
        line = output_lines[index]
        delimiter_index = line.find("\"") + 1
        vpn_name = line[delimiter_index:line.find("\"", delimiter_index)]
        vpn_names.append(vpn_name)
    else:
        if properties.VPN_SORT_NAMES:
            vpn_names.sort()
        return vpn_names


def is_vpn_has_status(vpn_name, status):
    return status == utils.execute_cmd('networksetup -showpppoestatus "{}"'.format(vpn_name))


def connect_vpn(vpn_name):
    return utils.execute_cmd('networksetup -connectpppoeservice "{}"'.format(vpn_name))


def disconnect_vpn(vpn_name):
    return utils.execute_cmd('networksetup -disconnectpppoeservice "{}"'.format(vpn_name))


def connect(vpn_name):
    utils.display_notification(vpn_name, 'Connecting  🐾 🚀')
    connect_vpn(vpn_name)

    if utils.wait_until_condition(lambda: is_vpn_has_status(vpn_name, VPN_CONNECTED_STATUS),
                                  properties.VPN_SWITCH_RETRY_ATTEMPTS, properties.VPN_SWITCH_RETRY_BACKOFF):
        utils.display_notification(vpn_name, 'Connected  🚀 🟢')
        return True
    else:
        utils.display_notification(vpn_name, 'Connection failed  🚀 🔴')
        return False


def disconnect(vpn_name, display_notifications):
    if display_notifications:
        utils.display_notification(vpn_name, 'Disconnecting  🐾 💣')
    disconnect_vpn(vpn_name)

    if utils.wait_until_condition(lambda: is_vpn_has_status(vpn_name, VPN_DISCONNECTED_STATUS),
                                  properties.VPN_SWITCH_RETRY_ATTEMPTS, properties.VPN_SWITCH_RETRY_BACKOFF):
        if display_notifications:
            utils.display_notification(vpn_name, 'Disconnected  💣 🟢')
    else:
        utils.display_notification(vpn_name, 'Disconnection failed  💣 🔴')


def reconnect(vpn_name):
    utils.display_notification(vpn_name, 'Reconnecting  🐾 🎲')
    disconnect(vpn_name, False)
    return connect(vpn_name)


def enable_vpn(is_vpn_enabled, set_running_state, vpn_name, user_name):
    set_running_state(True)
    connection_established = False
    interruption_detected = False

    while is_vpn_enabled():
        internet_connected = utils.is_internet_connected()

        # connects to the VPN, for the current user
        if utils.is_user_active(user_name) \
                and internet_connected \
                and is_vpn_has_status(vpn_name, VPN_DISCONNECTED_STATUS):
            if connect(vpn_name):
                connection_established = True
                interruption_detected = False

        # reconnects to the VPN, for the current user
        elif utils.is_user_active(user_name) \
                and not internet_connected \
                and is_vpn_has_status(vpn_name, VPN_CONNECTED_STATUS):
            if reconnect(vpn_name):
                connection_established = True
                interruption_detected = False

        # disconnects from the VPN, for other users
        elif not utils.is_user_active(user_name) \
                and is_vpn_has_status(vpn_name, VPN_CONNECTED_STATUS):
            disconnect(vpn_name, True)
            connection_established = False

        # notifies when interrupted due to loss of internet connection
        elif utils.is_user_active(user_name) \
                and not internet_connected \
                and not is_vpn_has_status(vpn_name, VPN_CONNECTED_STATUS) \
                and connection_established \
                and not interruption_detected:
            utils.display_notification(vpn_name, 'Interrupted  🐾 💥')
            interruption_detected = True

        time.sleep(properties.VPN_MANAGE_CONNECTION_POLLING_SECONDS)
    else:
        if is_vpn_has_status(vpn_name, VPN_CONNECTED_STATUS):
            disconnect(vpn_name, True)

        set_running_state(False)


def enable_vpn_async(is_vpn_enabled, set_running_state, vpn_name, user_name):
    thread = threading.Thread(target=lambda: enable_vpn(is_vpn_enabled, set_running_state, vpn_name, user_name),
                              daemon=True)
    thread.start()
    return thread
