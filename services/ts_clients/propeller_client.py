from services.ts_clients.ts_client import TrafficSourceClient
from services import requests_manager
import requests
import json
import os


class PropellerClient(TrafficSourceClient):
    def __init__(self):
        super().__init__(
            network_fullname="PropellerAds",
            network_alias="prop",
            interface="api",
            access_token=os.getenv("PROPELLER_ACCESS_TOKEN"))

    def get_balance(self):
        """
        Get PropellerAds balance.

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

        try:
            return float(balance_response.json())
        except json.JSONDecodeError as decode_error:
            self._logger.error(
                f"Decode error occurred while trying to parse balance response for propeller, doc:"
                f"{decode_error.doc}"
            )
            return
        except TypeError:
            self._logger.error(f"Can't convert balance to float, value: {balance_response.json()}")
