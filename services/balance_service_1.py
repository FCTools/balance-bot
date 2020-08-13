from services.ts_clients.clients import *

class BalanceService:
    def __init__(self):
        self._clients = [
            DaoPushClient(),
            EvadavClient(),
            PropellerClient(),
            PushHouseClient()
        ]

        self._balances_checking_interval = float(os.getenv("BALANCES_CHECKING_INTERVAL", 900))  # seconds

    def set_notifications_interval(self, chat_id, interval):
        """
        Set given interval between balance notifications.

        :param chat_id: chat id
        :type chat_id: int

        :param interval: notifications interval to set (in hours)
        :type interval: float

        :return: None
        """

        for client in self._clients:
            client.notifications_interval = interval

        self._sender.send_message(chat_id, "Success.")

    def check_balances(self):
        """
        Checks balances and send notifications in infinite loop.

        :return: None
        """

        while True:
            for client in self._clients:
                client.check_balance()

            time.sleep(self._balances_checking_interval)
