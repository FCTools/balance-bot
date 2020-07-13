from services.database_cursor import Database
from services.sender import Sender


class UpdateHandler:
    def __init__(self, telegram_access_token):
        self._sender = Sender(telegram_access_token)
        self._database = Database()

        self._available_commands = [
            "set_info_balance",
            "set_warning_balance",
            "set_critical_balance",
            "get_balance",
            "start",
            "help",
        ]

        self._available_networks = ["propeller"]

    def is_authorized(self, chat_id):
        users_list = self._database.get_users()

        for user in users_list:
            if chat_id == user["chat_id"]:
                return True

        return False

    def handle_command(self, command):
        print(command)
        chat_id = command["message"]["from"]["id"]

        if self.is_authorized(chat_id):
            print(command)
        else:
            pass  # permission denied

    def _set_balance_value(self, level, balance):
        pass

    def _get_balance(self, network):
        pass

    def _start(self):
        pass

    def _help(self):
        pass
