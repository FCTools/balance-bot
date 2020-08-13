"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import requests


class Updater:
    """
    Service for telegram updates getting.
    """

    def __init__(self, telegram_access_token):
        self._requests_url = f"https://api.telegram.org/bot{telegram_access_token}/"

    def get_updates(self, offset=None, timeout=10):
        """
        Get updates list from telegram.

        :param offset: offset (last update id)
        :type offset: int

        :param timeout: timeout
        :type timeout: int

        :return: updates list
        :rtype: list
        """

        method = "getUpdates"

        updates = requests.get(self._requests_url + method, params={"offset": offset, "timeout": timeout}).json()

        if "result" in updates:
            return updates["result"]

        return []
