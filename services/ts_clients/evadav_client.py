"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import json
import os

import requests

from services.helpers import requests_manager
from services.ts_clients.ts_client import TrafficSourceClient


class EvadavClient(TrafficSourceClient):
    def __init__(self, telegram_access_token):
        super().__init__(
            telegram_access_token=telegram_access_token,
            network_fullname="Evadav",
            network_alias="eva",
            interface="api",
            access_token=os.getenv("EVADAV_ACCESS_TOKEN"))

    def get_balance(self):
        """
        Get Evadav balance.

        :return: balance or None
        :rtype: Union[None, float]
        """

        balance_response = requests_manager.get(requests.Session(), f"https://evadav.com/api/v2.0/account/balance",
                                                params={"access-token": self._access_token},
                                                headers={"accept": "application/json"})

        if not isinstance(balance_response, requests.Response):
            self._logger.error(f"Error occurred while trying to get balance from eva: {balance_response}")
            return
        if balance_response.status_code != 200:
            self._logger.error(f"Can't get eva balance: get response with status code {balance_response.status_code}." \
                               f"Response: {balance_response.text}")
            return

        try:
            balance_response_json = balance_response.json()
        except json.JSONDecodeError as decode_error:
            self._logger.error(
                f"Decode error occurred while trying to parse balance response for evadav, doc:" f"{decode_error.doc}"
            )
            return

        try:
            return balance_response_json["data"]["advertiser"]
        except KeyError:
            self._logger.error(
                f"KeyError occurred while trying to get eva balance from balance_response_json. "
                f"Value: {balance_response_json}"
            )
