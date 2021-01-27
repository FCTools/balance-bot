# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of balance-bot project.
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

from services.working_loop import WorkingLoop

try:
    WorkingLoop().start()
except KeyboardInterrupt:
    exit(0)
