"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import json
import os

import requests

from services import requests_manager
from services.ts_clients.ts_client import TrafficSourceClient


class MgidClient(TrafficSourceClient):
    def __init__(self, telegram_access_token):
        self._client_id = os.getenv("MGID_CLIENT_ID")

        super().__init__(
            telegram_access_token=telegram_access_token,
            network_fullname="MGID",
            network_alias="mgid",
            interface="api",
            access_token=os.getenv("MGID_ACCESS_TOKEN"))

    def get_balance(self):
        """
        Get MGID balance.

        :return: balance or None
        :rtype: Union[None, float]
        """

        balance_response = requests_manager.get(requests.Session(),
                                                f"https://api.mgid.com/v1/clients/{self._client_id}",
                                                params={"token": self._access_token},
                                                headers={"accept": "application/json"})

        if not isinstance(balance_response, requests.Response):
            self._logger.error(f"Error occurred while trying to get balance from mgid: {balance_response}")
            return
        if balance_response.status_code != 200:
            self._logger.error(f"Can't get mgid balance: get response with status code {balance_response.status_code}."
                               f"Response: {balance_response.text}")
            return

        try:
            balance_response_json = balance_response.json()
        except json.JSONDecodeError as decode_error:
            self._logger.error(
                f"Decode error occurred while trying to parse balance response for MGID, doc:" f"{decode_error.doc}"
            )
            return

        try:
            return balance_response_json["wallet"]["balance"]
        except KeyError:
            self._logger.error(
                f"KeyError occurred while trying to get MGID balance from balance_response_json. "
                f"Value: {balance_response_json}"
            )
