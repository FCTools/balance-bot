from services.balance_service import BalanceService
from services.database_cursor import Database
from services.sender import Sender


class UpdateHandler:
    def __init__(self, telegram_access_token):
        self._sender = Sender(telegram_access_token)
        self._database = Database()
        self._balance_service = BalanceService(telegram_access_token)

        self._available_commands = [
            "set_info_balance",
            "set_warning_balance",
            "set_critical_balance",
            "get_balance",
            "start",
            "help",
        ]

        self._available_networks = ["prop", "eva", "pushhouse"]
        self._available_notification_levels = ['info', 'warning', 'critical']

    @staticmethod
    def _network_alias_to_name(alias):
        if alias == 'prop':
            return 'PropellerAds'
        elif alias == 'eva':
            return 'Evadav'
        elif alias == 'pushhouse':
            return 'Push.house'

        return 'Unknown'

    def is_authorized(self, chat_id):
        users_list = self._database.get_users()

        for user in users_list:
            if chat_id == user["chat_id"]:
                return True

        return False

    def handle_command(self, command):
        chat_id = command["message"]["from"]["id"]

        if self.is_authorized(chat_id):
            command_text = command["message"]["text"].strip()

            if not command_text.startswith("/") or command_text[1:].split()[0] not in self._available_commands:
                self._sender.send_message(
                    chat_id, "Unknown command. You can get list of available commands using /help."
                )
                return

            command_text = command_text[1:].split()

            if command_text[0] == "start":
                self._start(chat_id)
            elif command_text[0] == "help":
                self._help(chat_id)
            elif command_text[0] in ["set_info_balance", "set_warning_balance", "set_critical_balance"]:
                level = command_text[0].split('_')[1]
                self._set_balance_value(chat_id, level, *command_text[1:])
            elif command_text[0] == "get_balance":
                if len(command_text) < 2:
                    self._get_balance(chat_id, "")
                else:
                    self._get_balance(chat_id, command_text[1])

        else:
            self._sender.send_message(chat_id, "Permission denied.")

    def balance_is_valid(self, network, level, balance_to_set):
        network = self._network_alias_to_name(network)
        current_levels = self._database.get_notification_levels(network)

        if level == 'info':
            warning_balance = current_levels['warning']

            if balance_to_set < warning_balance:
                return False, "Balance for info-level can't be less or equal than balance for warning-level."
        elif level == 'warning':
            info_balance = current_levels['info']
            critical_balance = current_levels['critical']

            if balance_to_set >= info_balance:
                return False, "Balance for warning-level can't be greater or equal than balance for info-level."
            elif balance_to_set <= critical_balance:
                return False, "Balance for warning level can't be less or equal than balance for critical-level."
        elif level == 'critical':
            warning_balance = current_levels['warning']

            if balance_to_set >= warning_balance:
                return False, "Balance for critical-level can't be greater or equal than balance for warning-level."

        return True, "OK"

    def _set_balance_value(self, chat_id, level, *args):
        if len(args) < 2:
            self._sender.send_message(chat_id, 'Incorrect number of arguments.')
            return

        network = args[0]
        balance = args[1]

        if network not in self._available_networks:
            self._sender.send_message(chat_id, 'Incorrect network. I support only prop, pushhouse and eva.')
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
        else:
            self._get_balance(chat_id, "prop")
            self._get_balance(chat_id, "eva")
            self._get_balance(chat_id, "pushhouse")
            return

        if balance:
            self._sender.send_message(chat_id, f"<b>{network_name}</b> balance is {balance}$")
        else:
            self._sender.send_message(chat_id, "Sorry, something went wrong.")

    def _start(self, chat_id):
        self._sender.send_message(chat_id, "Hello!")

    def _help(self, chat_id):
        help_message_template = (
            "Hello!\nI support following networks:\n"
            "1. Propeller Ads (alias: prop)\n"
            "2. Push.house (alias: pushhouse)\n"
            "3. Evadav (alias: eva)\n\nI support following commands:\n\n"
            "1. /start - start message\n"
            "2. /help - this message\n\n"
            "3. /get_balance - returns current balance for selected network.\n\n"
            "<b>Format</b>: /get_balance <i>network_alias</i>\n\n"
            "   <i>network_alias</i> - optional, can be: prop, pushhouse or eva. "
            "If empty, returns balances for all networks."
        )

        self._sender.send_message(chat_id, help_message_template)
