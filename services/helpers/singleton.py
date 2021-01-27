# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of balance-bot project.
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>


class Singleton(type):
    """
    Metaclass for singleton pattern implementation.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
