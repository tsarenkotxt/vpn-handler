# -*- coding: utf-8 -*-

import threading
import time

import rumps

import properties
import settings_reader
import utils
import vpn_service

DEFAULT_VPN_ITEM = 'VPN not found'
FIRST_MENU_SEPARATOR = 'SeparatorMenuItem_1'
SECOND_MENU_SEPARATOR = 'SeparatorMenuItem_2'


class VpnHandler:

    def __init__(self):
        self.config = {
            "app_name": "VPN Handler (arm)",
            "default_title": "🔘",
            "vpn_active_title": "👽"
        }

        # general initialization
        self.app = rumps.App(self.config["app_name"])
        self.app.title = self.config["default_title"]
        self.user_name = utils.get_active_user()
        self.app.menu = ['User: ' + self.user_name, None]

        self.app_running = True
        self.active_vpn_threads = {}
        self.vpn_menu_items = {}  # vpn 'menu'
        self.connect_vpn_menu_items = {}  # vpn 'connect' buttons
        self.connect_on_startup_vpn_menu_items = {}  # vpn 'autoconnect' settings
        self.enabled_connect_on_startup_vpn_menu_items = []

        # vpn items initialization
        connect_on_startup_vpn_names = settings_reader.read_auto_connect_on_startup_vpn_names()
        for vpn_name in vpn_service.get_vpn_names():
            self.initialize_vpn_items(vpn_name, connect_on_startup_vpn_names)

        # preferences initialization
        self.initialize_preferences()

        # quit item initialization
        self.initialize_quit_button()

    def initialize_vpn_items(self, vpn_name, connect_on_startup_vpn_names, insertion_pointer=None):
        vpn_menu_item = rumps.MenuItem(title=vpn_name)
        vpn_menu_item.vpn_name = vpn_name
        self.vpn_menu_items[vpn_name] = vpn_menu_item

        connect_vpn_menu_item = rumps.MenuItem(title='Connect',
                                               callback=self.handle_vpn)
        connect_vpn_menu_item.vpn_name = vpn_name
        connect_vpn_menu_item.vpn_running = False
        vpn_menu_item.add(connect_vpn_menu_item)
        self.connect_vpn_menu_items[vpn_name] = connect_vpn_menu_item

        vpn_menu_item.add(None)
        auto_connect_vpn_menu_item = rumps.MenuItem(title='AutoConnect on startup',
                                                    callback=self.handle_auto_connecting_vpn_settings)
        auto_connect_vpn_menu_item.vpn_name = vpn_name
        vpn_menu_item.add(auto_connect_vpn_menu_item)
        self.connect_on_startup_vpn_menu_items[vpn_name] = auto_connect_vpn_menu_item

        if vpn_name in connect_on_startup_vpn_names:
            auto_connect_vpn_menu_item.state = True
            self.enabled_connect_on_startup_vpn_menu_items.append(connect_vpn_menu_item)

        if insertion_pointer is not None:
            self.app.menu.insert_after(insertion_pointer, vpn_menu_item)
        else:
            self.app.menu.add(vpn_menu_item)

    def initialize_preferences(self):
        self.app.menu.add(None)
        preferences_menu_item = rumps.MenuItem("Preferences")
        launch_app_on_startup_menu_item = rumps.MenuItem(title='Launch app on startup',
                                                         callback=self.handle_launch_app_on_startup_settings)
        launch_app_on_startup_menu_item.state = settings_reader.read_launch_app_on_startup()
        preferences_menu_item.add(launch_app_on_startup_menu_item)
        self.app.menu.add(preferences_menu_item)

    def initialize_quit_button(self):
        self.app.menu.add(None)
        self.app.quit_button = None
        self.app.menu.add(rumps.MenuItem(title='Quit',
                                         callback=self.handle_quit))

    def run(self):
        self.handle_vpn_threads_async()
        self.handle_auto_connecting_vpn_async()
        self.handle_already_connected_vpn_async()
        self.handle_network_preferences_async()
        self.app.run()

    def handle_vpn_threads(self):
        while self.app_running:
            if self.active_vpn_threads:
                self.app.title = self.config["vpn_active_title"]
            else:
                self.app.title = self.config["default_title"]

            for vpn_name, vpn_thread in list(self.active_vpn_threads.items()):  # iterates thread safe
                if not vpn_thread.is_alive():
                    self.active_vpn_threads.pop(vpn_name, None)
            else:
                time.sleep(properties.VPN_TRACK_THREADS_POLLING_SECONDS)

    def handle_vpn_threads_async(self):
        thread = threading.Thread(target=lambda: self.handle_vpn_threads(),
                                  daemon=True)
        thread.start()

    def handle_auto_connecting_vpn(self):
        for menu_item in list(self.enabled_connect_on_startup_vpn_menu_items):  # iterates thread safe
            connect_vpn_menu_item = self.connect_vpn_menu_items.get(menu_item.vpn_name)
            if connect_vpn_menu_item is not None:
                self.handle_vpn(connect_vpn_menu_item)

    def handle_auto_connecting_vpn_async(self):
        thread = threading.Thread(target=lambda: self.handle_auto_connecting_vpn(),
                                  daemon=True)
        thread.start()

    def handle_already_connected_vpn(self):
        while self.app_running:
            for menu_item in list(self.connect_vpn_menu_items.values()):  # iterates thread safe
                if not menu_item.state \
                        and not menu_item.vpn_running \
                        and vpn_service.is_vpn_has_status(menu_item.vpn_name, vpn_service.VPN_CONNECTED_STATUS):
                    self.handle_vpn(menu_item)
            else:
                time.sleep(properties.VPN_TRACK_CONNECTIONS_POLLING_SECONDS)

    def handle_already_connected_vpn_async(self):
        thread = threading.Thread(target=lambda: self.handle_already_connected_vpn(),
                                  daemon=True)
        thread.start()

    def handle_vpn_list_changes(self, removed_vpn_names, added_vpn_names):
        for vpn_name in removed_vpn_names:
            utils.display_notification(vpn_name, 'Removing VPN 🐾 ❌')
            self.app.menu.pop(vpn_name, None)
            self.vpn_menu_items.pop(vpn_name, None)
            self.connect_on_startup_vpn_menu_items.pop(vpn_name, None)
            menu_item = self.connect_vpn_menu_items.pop(vpn_name, None)
            if menu_item is not None:
                menu_item.state = False

        for vpn_name in added_vpn_names:
            # inserts the new vpn item & keep sorted vpn items
            if properties.VPN_SORT_NAMES:
                insertion_pointer = FIRST_MENU_SEPARATOR
                first_menu_separator_found = False

                for menu_item_key in list(self.app.menu.keys()):  # iterates thread safe
                    if menu_item_key == FIRST_MENU_SEPARATOR:
                        first_menu_separator_found = True

                    if not first_menu_separator_found:
                        continue
                    elif menu_item_key == SECOND_MENU_SEPARATOR:
                        break

                    if menu_item_key <= vpn_name:
                        # moves the new vpn item after the target menu item
                        insertion_pointer = menu_item_key
                    else:
                        continue

                self.initialize_vpn_items(vpn_name, settings_reader.read_auto_connect_on_startup_vpn_names(),
                                          insertion_pointer)
            else:
                # adds the new vpn item as first to the menu
                self.initialize_vpn_items(vpn_name, settings_reader.read_auto_connect_on_startup_vpn_names(),
                                          FIRST_MENU_SEPARATOR)
            utils.display_notification(vpn_name, 'Detected new VPN  🐾 👀')

    def handle_network_preferences(self):
        while self.app_running:
            if len(self.app.menu) == 6:
                self.app.menu.insert_after(FIRST_MENU_SEPARATOR, DEFAULT_VPN_ITEM)
            elif len(self.app.menu) > 7 and DEFAULT_VPN_ITEM in self.app.menu.keys():
                self.app.menu.pop(DEFAULT_VPN_ITEM, None)

            current_vpn_names = list(self.vpn_menu_items.keys())  # iterates thread safe
            latest_vpn_names = vpn_service.get_vpn_names()

            removed_vpn_names = []
            for vpn_name in current_vpn_names:
                if vpn_name not in latest_vpn_names:
                    removed_vpn_names.append(vpn_name)

            added_vpn_names = []
            for vpn_name in latest_vpn_names:
                if vpn_name not in current_vpn_names:
                    added_vpn_names.append(vpn_name)

            self.handle_vpn_list_changes(removed_vpn_names, added_vpn_names)
            time.sleep(properties.VPN_TRACK_PREFERENCES_POLLING_SECONDS)

    def handle_network_preferences_async(self):
        thread = threading.Thread(target=lambda: self.handle_network_preferences(),
                                  daemon=True)
        thread.start()

    def handle_vpn(self, sender):
        if not sender.state:
            sender.state = True
            vpn_thread = vpn_service.enable_vpn_async(lambda: sender.state,
                                                      lambda vpn_running: setattr(sender, 'vpn_running', vpn_running),
                                                      sender.vpn_name, self.user_name)
            self.active_vpn_threads[sender.vpn_name] = vpn_thread
        else:
            sender.state = False

    def handle_auto_connecting_vpn_settings(self, sender):
        if not sender.state:
            sender.state = True
        else:
            sender.state = False

        connect_on_startup_vpn_names = []
        for menu_item in list(self.connect_on_startup_vpn_menu_items.values()):  # iterates thread safe
            if menu_item.state:
                connect_on_startup_vpn_names.append(menu_item.vpn_name)
        else:
            settings_reader.write_auto_connect_on_startup_vpn_names(connect_on_startup_vpn_names)

    def handle_launch_app_on_startup_settings(self, sender):
        if not sender.state:
            sender.state = True
            settings_reader.write_launch_app_on_startup(True)
            utils.enable_launch_app_on_startup(self.config["app_name"])
        else:
            sender.state = False
            settings_reader.write_launch_app_on_startup(False)
            utils.disable_launch_app_on_startup(self.config["app_name"])

    def handle_quit(self, _):
        for menu_item in list(self.connect_vpn_menu_items.values()):  # iterates thread safe
            if menu_item.state:
                menu_item.state = False

        for vpn_name, vpn_thread in list(self.active_vpn_threads.items()):  # iterates thread safe
            if vpn_thread.is_alive():
                utils.wait_until_condition(
                    lambda: vpn_service.is_vpn_has_status(vpn_name, vpn_service.VPN_DISCONNECTED_STATUS),
                    properties.VPN_THREAD_QUIT_RETRY_ATTEMPTS, properties.VPN_THREAD_QUIT_RETRY_BACKOFF)

        self.app_running = False
        rumps.quit_application()


if __name__ == '__main__':
    handler = VpnHandler()
    handler.run()
