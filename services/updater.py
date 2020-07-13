import requests


class Updater:
    def __init__(self, telegram_access_token):
        self._requests_url = f"https://api.telegram.org/bot{telegram_access_token}/"

    def get_updates(self, offset=None, timeout=10):
        method = "getUpdates"

        updates = requests.get(self._requests_url + method, params={"offset": offset, "timeout": timeout}).json()

        if "result" in updates:
            return updates["result"]

        return []
