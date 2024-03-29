# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of balance-bot project.
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

import json
import os

import requests

from services.helpers import requests_manager
from services.ts_clients.ts_client import TrafficSourceClient


class PropellerClient(TrafficSourceClient):
    def __init__(self, telegram_access_token):
        super().__init__(
            telegram_access_token=telegram_access_token,
            network_fullname="PropellerAds",
            network_alias="prop",
            interface="api",
            access_token=os.getenv("PROPELLER_ACCESS_TOKEN"))

    def get_balance(self):
        """
        Get Propeller Ads balance.

        :return: balance or None
        :rtype: Union[None, float]
        """

        balance_response = requests_manager.get(
            requests.Session(),
            "https://ssp-api.propellerads.com/v5/adv/balance",
            headers={"Authorization": f"Bearer {self._access_token}",
                     "Accept": "application/json"},
        )

        if not isinstance(balance_response, requests.Response):
            self._logger.error(f"Error occurred while trying to get propeller balance: {balance_response}")
            return

        if balance_response.status_code != 200:
            self._logger.error(
                f"Balance response for propeller with non-success status code: {balance_response.status_code}."
                f"Response: {balance_response.json()}")
            return False

        try:
            return float(balance_response.json())
        except json.JSONDecodeError as decode_error:
            self._logger.error(
                f"Decode error occurred while trying to parse balance response for propeller, doc:"
                f"{decode_error.doc}"
            )
            return
        except TypeError:
            self._logger.error(f"Can't convert this balance value to float: {balance_response.json()}")
