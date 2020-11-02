"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import logging

from services.balance_service import BalanceService
from services.database_cursor import Database
from services.sender import Sender


class UpdateHandler:
    """
    Class for telegram updates handling.
    """

    def __init__(self, telegram_access_token):
        self._logger = logging.getLogger("WorkingLoop.UpdateHandler")

        self._sender = Sender(telegram_access_token)
        self._database = Database()
        self._balance_service = BalanceService(telegram_access_token)

        self._available_commands = [
            "/set_info_balance",
            "/set_warning_balance",
            "/set_critical_balance",
            "/get_balance",
            "/set_notifications_interval",
            "/disable",
            "/enable",
            "/start",
            "/help",
        ]

        self._available_networks = ["dao", "eva", "prop", "zero", "mgid", "pushhouse", "kadam"]
        self._available_notification_levels = ["info", "warning", "critical"]
        self._help_message = self._read_help_message()

        self._logger.info("UpdateHandler was successfully initialized.")

    @staticmethod
    def _read_help_message():
        """
        Read help-message from README and format it according to telegram formatting options.

        :return: formatted message
        :rtype: str
        """

        with open("README.md", "r", encoding="utf-8") as file:
            return (
                file.read()
                    .replace("#", "\#")
                    .replace("/", "\/")
                    .replace("-", "\-")
                    .replace(".", "\.")
                    .replace("(", "\(")
                    .replace(")", "\)")
                    .replace("[", "\[")
                    .replace("]", "\]")
                    .replace("_", "\_")
            )

    @staticmethod
    def _network_alias_to_name(alias):
        """
        Convert network alias to network fullname.

        :param alias: network alias to convert
        :type alias: str

        :return: network fullname
        :rtype: str
        """

        if alias == "prop":
            return "PropellerAds"
        elif alias == "eva":
            return "Evadav"
        elif alias == "pushhouse":
            return "Push.house"
        elif alias == "dao":
            return "DaoPush"
        elif alias == "zero":
            return "ZeroPark"
        elif alias == "mgid":
            return "MGID"
        elif alias == "kadam":
            return "Kadam"

        return "Unknown"

    @staticmethod
    def is_command(update):
        """
        Return True if given update is bot command, else False.

        :param update: update
        :type update: dict

        :return: True/False
        :rtype: bool
        """

        return (
                "message" in update
                and "entities" in update["message"]
                and update["message"]["entities"][0]["type"] == "bot_command"
        )

    @staticmethod
    def extract_chat_id(update):
        """
        Extract sender chat id from given update.

        :param update: update
        :type update: dict

        :return: chat id if success, else None
        :rtype: Union[int, None]
        """

        if "message" in update and "from" in update["message"] and "id" in update["message"]["from"]:
            return update["message"]["from"]["id"]

    def command_is_valid(self, update):
        """
        Check that given update is valid command.

        :param update: update to check
        :type update: dict

        :return: True if given update is valid command, else False
        :rtype: bool
        """

        chat_id = self.extract_chat_id(update)

        if not chat_id:
            self._logger.warning(f"Can't extract chat_id from json-package: {update}")
            return False

        if not self.is_command(update):
            self._logger.info(f"Get non-command update: {update}")
            self._sender.send_message(chat_id, "I support only commands. Use /help for details.")
            return False

        if not self._database.is_authorized(chat_id):
            self._logger.warning(f"Message from unauthorized user: {update}")
            self._sender.send_message(chat_id, "Permission denied.")
            return False

        return True

    def handle_command(self, update):
        """
        Handle given telegram update.

        :param update: update to handle
        :type update: dict

        :return: None
        """

        if not self.command_is_valid(update):
            return

        chat_id = self.extract_chat_id(update)
        command_parts = update["message"]["text"].strip().split()

        command = command_parts[0]
        args = command_parts[1:]

        if command not in self._available_commands:
            self._sender.send_message(chat_id, "Unknown command. You can get list of available commands using /help.")
            return

        if command == "/start":
            self._start(chat_id)

        elif command == "/help":
            self._help(chat_id)

        elif command in ["/set_info_balance", "/set_warning_balance", "/set_critical_balance"]:
            level = command.split("_")[1]
            self._set_balance_value(chat_id, level, *args)

        elif command == "/get_balance":
            if not args:
                self._get_balance(chat_id, "")
            elif len(args) == 1:
                self._get_balance(chat_id, args[0])
            else:
                self._sender.send_message(chat_id, f"Invalid number of arguments (expected 0 or 1, got {len(args)}).")

        elif command == "/set_notifications_interval":
            if not args:
                self._sender.send_message(chat_id, f"Please specify interval in hours (min: 0.34, max: 24).")
            elif len(args) == 1:
                self._set_notifications_interval(chat_id, args[0])
            else:
                self._sender.send_message(chat_id, f"Invalid number of arguments (expected 1, got {len(args)}).")

        elif command == '/disable':
            if not args:
                self._sender.send_message(chat_id, f"Please specify network to disable.")
            elif len(args) == 1:
                if args[0] in self._available_networks:
                    self._disable(chat_id, args[0])
                else:
                    self._sender.send_message(chat_id, f"Invalid network: {args[0]}.")
            else:
                self._sender.send_message(chat_id, f"Invalid number of arguments (expected 1, got {len(args)}).")

        elif command == '/enable':
            if not args:
                self._sender.send_message(chat_id, f"Please specify network to enable")
            elif len(args) == 1:
                if args[0] in self._available_networks:
                    self._enable(chat_id, args[0])
                else:
                    self._sender.send_message(chat_id, f"Invalid network: {args[0]}.")
            else:
                self._sender.send_message(chat_id, f"Invalid number of arguments (expected 1, got {len(args)}).")

    def balance_is_valid(self, network, level, balance_to_set):
        """
        Check that given border-balance for given network and notification level is valid (can be set without errors).

        :param network: network alias
        :type network: str

        :param level: notification level
        :type level: str

        :param balance_to_set: balance to set
        :type balance_to_set: float

        :return: True if balance is valid, else False
        :rtype: bool
        """

        network = self._network_alias_to_name(network)
        success, current_levels = self._database.get_notification_levels(network)

        if not success:
            self._logger.error(f"Database error occurred while trying to get notification levels: {current_levels}")
            return False

        if level == "info":
            warning_balance = current_levels["warning"]

            if balance_to_set < warning_balance:
                return False, "Balance for info-level can't be less or equal than balance for warning-level."
        elif level == "warning":
            info_balance = current_levels["info"]
            critical_balance = current_levels["critical"]

            if balance_to_set >= info_balance:
                return False, "Balance for warning-level can't be greater or equal than balance for info-level."
            elif balance_to_set <= critical_balance:
                return False, "Balance for warning level can't be less or equal than balance for critical-level."
        elif level == "critical":
            warning_balance = current_levels["warning"]

            if balance_to_set >= warning_balance:
                return False, "Balance for critical-level can't be greater or equal than balance for warning-level."

        return True, "OK"

    def _set_balance_value(self, chat_id, level, *args):
        """
        Set border-balance for given notification level.

        :param chat_id: user chat id
        :type chat_id: int

        :param level: notification level
        :type level: str

        :return: None
        """

        if len(args) != 2:
            self._sender.send_message(chat_id, f"Incorrect number of arguments (expected 2, got {len(args)}).")
            return

        network = args[0]
        balance = args[1]

        if network not in self._available_networks:
            self._sender.send_message(chat_id, "Incorrect network. Use /help to get list of supported networks.")
            return

        try:
            balance = float(balance)
        except TypeError:
            self._sender.send_message(chat_id, "Incorrect balance value (can't convert it to real number).")
            return

        balance_is_correct, error_message = self.balance_is_valid(network, level, balance)

        if not balance_is_correct:
            self._sender.send_message(chat_id, error_message)
            return

        self._database.set_notification_level_balance(self._network_alias_to_name(network), level, balance)
        self._sender.send_message(chat_id, "Success.")

    def _get_balance(self, chat_id, network_alias):
        """
        Handle /get_balance command.

        :param chat_id: sender chat id
        :type chat_id: int

        :param network_alias: network alias
        :type network_alias: str

        :return: None
        """

        if network_alias and network_alias not in self._available_networks:
            self._sender.send_message(chat_id, "Incorrect network. Use /help to get list of supported networks.")
            return

        if not network_alias:
            for network in self._available_networks:
                self._get_balance(chat_id, network)
            return

        balance = self._balance_service.get_balance(network_alias)
        network_name = self._network_alias_to_name(network_alias)

        if balance == "Now authorizing.":
            self._sender.send_message(chat_id,
                                      f"Trying to solve CAPTCHA for Push.house authorization. Please, try again later.")
            return

        if balance:
            self._sender.send_message(chat_id, f"<b>{network_name}</b> balance is {balance}$")
        else:
            self._sender.send_message(chat_id,
                                      "Sorry, something went wrong. Try again later or/and contact developers.")

    def _set_notifications_interval(self, chat_id, interval):
        """
        Handle /set_notifications_interval command.

        :param chat_id: sender chat id
        :type chat_id: int

        :param interval: interval to set in hours
        :type interval: float

        :return: None
        """

        try:
            interval = float(interval)
        except TypeError:
            self._sender.send_message(chat_id, "Incorrect interval (not a number).")
            return

        if not (0.34 <= interval <= 24):
            self._sender.send_message(chat_id, "Interval must be from 0.34 to 24.")
            return

        self._balance_service.set_notifications_interval(chat_id, interval)

    def _disable(self, chat_id, network_alias):
        """
        Disable notifications for selected network.

        :param chat_id: sender chat id
        :type chat_id: int

        :param network_alias: network alias
        :type network_alias: str

        :return: None
        """

        self._database.set_network_status("disabled", self._network_alias_to_name(network_alias))
        self._sender.send_message(chat_id, "Success.")

    def _enable(self, chat_id, network_alias):
        """
        Enable notifications for selected network.

        :param chat_id: sender chat id
        :type chat_id: int

        :param network_alias: network alias
        :type network_alias: str

        :return: None
        """

        self._database.set_network_status("enabled", self._network_alias_to_name(network_alias))
        self._sender.send_message(chat_id, "Success.")

    def _start(self, chat_id):
        """
        Send greeting to user.

        :param chat_id: sender chat id
        :type chat_id: int

        :return: None
        """

        self._sender.send_message(chat_id, "Hello!")

    def _help(self, chat_id):
        """
        Send help message to user.

        :param chat_id: sender chat_id
        :type chat_id: int

        :return: None
        """

        self._sender.send_message(chat_id, self._help_message, parse_mode="MarkdownV2")
