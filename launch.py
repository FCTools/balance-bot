"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

from services.working_loop import WorkingLoop

try:
    WorkingLoop().start()
except KeyboardInterrupt:
    exit(0)
