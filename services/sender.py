import requests


class Sender:
    def __init__(self, telegram_access_token):
        self._requests_url = f"https://api.telegram.org/bot{telegram_access_token}/"

    def send_message(self, to, text):
        method = "sendMessage"

        response = requests.post(self._requests_url + method, params={"chat_id": to, "text": text,
                                                                      "parse_mode": "HTML"})
