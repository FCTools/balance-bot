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
    def __init__(self):
        telegram_access_token = os.environ.get("TELEGRAM_ACCESS_TOKEN")

        self._logger = logging.getLogger("WorkingLoop")
        self._configure_logger()

        self._updater = Updater(telegram_access_token)
        self._update_handler = UpdateHandler(telegram_access_token)
        self._balance_service = BalanceService(telegram_access_token)

        self._lock = threading.Lock()
        self._updates_queue = Queue()

        self._logger.info("WorkingLoop initialized.")

    def _configure_logger(self):
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

    def _listen_for_updates(self):
        offset = None

        while True:
            updates_list = self._updater.get_updates(offset)

            for update in updates_list:
                with self._lock:
                    self._updates_queue.put(update)

                offset = update["update_id"] + 1

    def _handle_updates(self):
        while True:
            if not self._updates_queue.empty():
                with self._lock:
                    update = self._updates_queue.get()
                    print(update)
            else:
                time.sleep(3)
                continue

            self._update_handler.handle_command(update)

    def start(self):
        self._logger.info("WorkingLoop started.")

        handling_thread = threading.Thread(target=self._handle_updates, daemon=True)
        balances_check_thread = threading.Thread(target=self._balance_service.check_balances, daemon=True)

        handling_thread.start()
        balances_check_thread.start()

        self._logger.info("Start handling updates and balances checking.")

        self._logger.info("Start listening for updates.")
        self._listen_for_updates()
