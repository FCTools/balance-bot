from services.database_cursor import Database
import logging


class TrafficSourceClient:
    def __init__(self, network_fullname, network_alias, interface, **kwargs):
        self._logger = logging.getLogger(f"WorkingLoop.BalanceService.{network_fullname}Client")

        self._last_notification_level = None
        self._last_notificaton_sending_time = None
        self._database = Database()
        self._network_fullname = network_fullname
        self._network_alias = network_alias

        if interface == "api":
            if "access_token" in kwargs:
                self._access_token = kwargs["access_token"]
            else:
                self._logger.error(f"Interface for network {network_fullname} is "\
                                   "api, but can't find access token in kwargs.")
                exit(-1)
        elif interface == "web":
            self._session = None

            if "login" in kwargs:
                self._login = kwargs["login"]
            else:
                self._logger.error(f"Interface for network {network_fullname} is "\
                                   "web, but can't find login in kwargs.")
                exit(-1)

            if "password" in kwargs:
                self._password = kwargs["password"]
            else:
                self._logger.error(f"Interface for network {network_fullname} is "\
                                   "web, but can't find password in kwargs.")
                exit(-1)
        else:
            self._logger.error(f"Incorrect network interface: {interface}")
            exit(-1)

    def _authorize(self):
        pass

    def _session_is_active(self):
        pass

    def get_balance(self):
        pass

    def send_status_message(self, balance, level):
        """
        Sends notification about balance.

        :param network: network alias
        :type network: str

        :param balance: balance
        :type balance: float

        :param level: notification level
        :type level: str

        :return: None
        """

        message = f"<b>{level.upper()}</b>: {self._network} balance is {balance}$"
        success, users_list = self._database_cursor.get_users()

        if not success:
            self._logger.error(f"Database error occurred while trying to get users: {users_list}")
            return

        for user in users_list:
            self._sender.send_message(user["chat_id"], message)

        self._last_notification_level = level
        self._last_notificaton_sending_time = datetime.utcnow()

    def check_balance(self):
        """
        Checks given balance and sends notification if necessary.

        :param network: network alias
        :type network: str

        :param balance: balance
        :type balance: float

        :return: None
        """

        balance = self.get_balance()

        if balance is None:
            self._logger.error("Can't get balance.")
            return

        success, notification_levels = self._database_cursor.get_notification_levels(network)

        if not success:
            self._logger.error(f"Can't get notification levels from database: {notification_levels}")
            return

        notification_level = None
        last_balance = 10 ** 9  # just very big number

        for level in notification_levels:
            if last_balance > notification_levels[level] > balance:
                last_balance = notification_levels[level]
                notification_level = level

        if not notification_level:
            return

        if (
            not self._networks[network]["last_notification_sending_time"]
            or notification_level != self._networks[network]["last_notification"]
            or datetime.utcnow() - self._networks[network]["last_notification_sending_time"]
            > timedelta(hours=self._notifications_interval)
        ):
            self.send_status_message(balance, notification_level)