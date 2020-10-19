"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import requests


def catch_network_errors(method):
    """
    Decorator for network errors catching.
    """

    def inner(*args, **kwargs):
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

    return inner


@catch_network_errors
def get(session, *args, **kwargs):
    """
    Make safe GET response using given session and arguments.

    :param session: session for response making
    :type session: requests.Session

    :return: response if success, else catch error
    :rtype: Union[requests.Response, Exception]
    """

    return session.get(*args, **kwargs)


@catch_network_errors
def post(session, *args, **kwargs):
    """
    Make safe POST response using given session and arguments.

    :param session: session for response making
    :type session: requests.Session

    :return: response if success, else catch error
    :rtype: Union[requests.Response, Exception]
    """

    return session.post(*args, **kwargs)
