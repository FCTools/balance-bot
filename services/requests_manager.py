import requests


def catch_network_errors(method):
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except requests.exceptions.HTTPError as exception:
            return exception

        except requests.exceptions.ConnectTimeout as exception:
            return exception

        except requests.exceptions.Timeout as exception:
            return exception

        except requests.exceptions.ConnectionError as exception:
            return exception

        except requests.exceptions.RequestException as exception:
            return exception

        except Exception as exception:
            return exception

    return wrapper


@catch_network_errors
def get(session, *args, **kwargs):
    return session.get(*args, **kwargs)


@catch_network_errors
def post(session, *args, **kwargs):
    return session.post(*args, **kwargs)
