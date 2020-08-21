"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import logging
import os
import platform
import threading
import time
from queue import Queue

from services.balance_service import BalanceService
from services.update_handler import UpdateHandler
from services.updater import Updater


class WorkingLoop:
    """
    Bot working loop.
    """

    def __init__(self):
        self._logger = logging.getLogger("WorkingLoop")
        self._configure_logger()

        environment_is_correct, errors_list = self._environment_is_correct()
        if not environment_is_correct:
            for error in errors_list:
                self._logger.critical(error)
            exit(-1)
        else:
            self._logger.info("Environment is correct.")

        telegram_access_token = os.environ.get("TELEGRAM_ACCESS_TOKEN")

        self._updater = Updater(telegram_access_token)
        self._update_handler = UpdateHandler(telegram_access_token)
        self._balance_service = BalanceService(telegram_access_token)

        self._lock = threading.Lock()
        self._updates_queue = Queue()

        self._logger.info("WorkingLoop was successfully initialized.")

    def _configure_logger(self):
        """
        Set logger basic configuration.
        """

        self._logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler("log.log", "w", "utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        file_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(file_handler)

        self._logger.info(f"Platform: {platform.system().lower()}")
        self._logger.info(f"WD: {os.getcwd()}")

        self._logger.info("Logger configured.")

    @staticmethod
    def _environment_is_correct():
        """
        Check that working environment is correct: all required environment variables and files exist.

        :return: status (True if all is correct, else False) and errors_list (empty if all is correct)
        :rtype: Tuple[Union[bool, list]]
        """

        correct = True
        errors = []

        required_files_list = ["user_agents.csv"]
        required_env_variables_list = [
            "TELEGRAM_ACCESS_TOKEN",
            "PROPELLER_ACCESS_TOKEN",
            "EVADAV_ACCESS_TOKEN",
            "PUSHHOUSE_EMAIL",
            "PUSHHOUSE_PASSWORD",
            "DAO_EMAIL",
            "DAO_PASSWORD",
            "CAPTCHA_SERVICE_KEY",
        ]

        for file in required_files_list:
            if not os.path.exists(file):
                correct = False
                errors.append("Can't find files with user agents list (user_agents.csv).")

        for env in required_env_variables_list:
            if not os.getenv(env):
                correct = False
                errors.append(f"Can't find required environment variable: {env}")

        return correct, errors

    def _listen_for_updates(self):
        """
        Method for infinite updates listening - target method for main thread.
        """

        offset = None

        while True:
            updates_list = self._updater.get_updates(offset)

            for update in updates_list:
                with self._lock:
                    self._updates_queue.put(update)

                offset = update["update_id"] + 1

    def _handle_updates(self):
        """
        Method for infinite updates handling - target method for HandlingThread.
        """

        while True:
            if not self._updates_queue.empty():
                with self._lock:
                    update = self._updates_queue.get()
                    print(update)
            else:
                time.sleep(2)
                continue

            self._update_handler.handle_command(update)

    def start(self):
        """
        Program ENTRY POINT is here. Create threads for updates handling and balances checking and start them.
        After that, listen for updates.
        """

        self._logger.info("WorkingLoop started.")

        handling_thread = threading.Thread(target=self._handle_updates, daemon=True, name="HandlingThread")
        balances_check_thread = threading.Thread(
            target=self._balance_service.check_balances, daemon=True, name="BalancesCheckingThread"
        )
        threading.current_thread().name = "ListeningThread"

        handling_thread.start()
        balances_check_thread.start()

        self._logger.info("Start handling updates and balances checking.")

        self._logger.info("Start listening for updates.")
        self._listen_for_updates()
