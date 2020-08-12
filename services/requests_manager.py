"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import requests


def catch_network_errors(method):
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException,
            Exception,
        ) as network_error:
            return network_error

    return wrapper


@catch_network_errors
def get(session, *args, **kwargs):
    return session.get(*args, **kwargs)


@catch_network_errors
def post(session, *args, **kwargs):
    return session.post(*args, **kwargs)
