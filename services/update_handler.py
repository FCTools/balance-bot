import logging

from services.balance_service import BalanceService
from services.database_cursor import Database
from services.sender import Sender


class UpdateHandler:
    def __init__(self, telegram_access_token):
        self._sender = Sender(telegram_access_token)
        self._database = Database()
        self._balance_service = BalanceService(telegram_access_token)

        self._logger = logging.getLogger("WorkingLoop.UpdateHandler")

        self._available_commands = [
            "/set_info_balance",
            "/set_warning_balance",
            "/set_critical_balance",
            "/get_balance",
            "/set_notifications_interval",
            "/start",
            "/help",
        ]

        self._available_networks = ["prop", "eva", "pushhouse", "dao"]
        self._available_notification_levels = ["info", "warning", "critical"]

        self._logger.info("UpdateHandler initialized.")

    @staticmethod
    def _network_alias_to_name(alias):
        if alias == "prop":
            return "PropellerAds"
        elif alias == "eva":
            return "Evadav"
        elif alias == "pushhouse":
            return "Push.house"
        elif alias == "dao":
            return "DaoPush"

        return "Unknown"

    def is_authorized(self, chat_id):
        success, users_list = self._database.get_users()

        if not success:
            self._logger.error(f"Database error occurred while trying to get users: {users_list}")
            return False

        for user in users_list:
            if chat_id == user["chat_id"]:
                return True

        return False

    @staticmethod
    def is_command(update):
        return (
            "message" in update
            and "entities" in update["message"]
            and update["message"]["entities"][0]["type"] == "bot_command"
        )

    @staticmethod
    def extract_chat_id(update):
        if "message" in update and "from" in update["message"] and "id" in update["message"]["from"]:
            return update["message"]["from"]["id"]

    def command_is_valid(self, update):
        chat_id = self.extract_chat_id(update)

        if not chat_id:
            self._logger.warning(f"Can't extract chat_id from json-package: {update}")
            return False

        if not self.is_command(update):
            self._logger.info(f"Get non-command update: {update}")
            self._sender.send_message(chat_id, "I support only commands. Use /help for details.")
            return False

        if not self.is_authorized(chat_id):
            self._logger.info(f"Message from unauthorized user: {update}")
            self._sender.send_message(chat_id, "Permission denied.")
            return False

        return True

    def handle_command(self, update):
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
                self._sender.send_message(chat_id, f"Please specify interval in hours (min: 0.34, max: 6).")
            elif len(args) == 1:
                self._set_notifications_interval(chat_id, args[0])
            else:
                self._sender.send_message(chat_id, f"Invalid number of arguments (expected 1, got {len(args)}).")

    def balance_is_valid(self, network, level, balance_to_set):
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
        if len(args) != 2:
            self._sender.send_message(chat_id, f"Incorrect number of arguments (expected 2, got {len(args)}).")
            return

        network = args[0]
        balance = args[1]

        if network not in self._available_networks:
            self._sender.send_message(chat_id, "Incorrect network. I support only prop, pushhouse and eva.")
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
        if network_alias and network_alias not in self._available_networks:
            self._sender.send_message(chat_id, "Incorrect network. I support only prop, pushhouse and eva.")
            return

        if network_alias == "prop":
            network_name = "PropellerAds"
            balance = self._balance_service.get_propeller_balance()
        elif network_alias == "eva":
            network_name = "Evadav"
            balance = self._balance_service.get_evadav_balance()
        elif network_alias == "pushhouse":
            network_name = "Push.house"
            balance = self._balance_service.get_pushhouse_balance()
        elif network_alias == "dao":
            network_name = "DaoPush"
            balance = self._balance_service.get_dao_balance()
        else:
            for network in self._available_networks:
                self._get_balance(chat_id, network)
            return

        if balance:
            self._sender.send_message(chat_id, f"<b>{network_name}</b> balance is {balance}$")
        else:
            self._sender.send_message(chat_id, "Sorry, something went wrong.")

    def _set_notifications_interval(self, chat_id, interval):
        try:
            interval = float(interval)
        except TypeError:
            self._sender.send_message(chat_id, "Incorrect interval (not a number).")
            return

        if not (0.34 <= interval <= 6):
            self._sender.send_message(chat_id, "Interval must be from 0.34 to 6.")
            return

        self._balance_service.set_notifications_interval(chat_id, interval)

    def _start(self, chat_id):
        self._sender.send_message(chat_id, "Hello!")

    def _help(self, chat_id):
        help_message_template = (
            "Hello!\nI support following networks:\n"
            "1. Propeller Ads (alias: prop)\n"
            "2. Push.house (alias: pushhouse)\n"
            "3. DaoPush (alias: dao)\n"
            "4. Evadav (alias: eva)\n\nI support following commands:\n\n"
            "1. /start - start message\n"
            "2. /help - this message\n\n"
            "3. /get_balance - returns current balance for selected network.\n\n"
            "<b>Format</b>: /get_balance <i>network_alias</i>\n\n"
            "   <i>network_alias</i> - optional, can be: prop, pushhouse or eva. "
            "If empty, returns balances for all networks."
        )

        self._sender.send_message(chat_id, help_message_template)
