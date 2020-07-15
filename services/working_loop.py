import os
import threading
import time
from queue import Queue

from services.balance_service import BalanceService
from services.update_handler import UpdateHandler
from services.updater import Updater


class WorkingLoop:
    def __init__(self):
        telegram_access_token = os.environ.get("TELEGRAM_ACCESS_TOKEN")
        self._updater = Updater(telegram_access_token)
        self._update_handler = UpdateHandler(telegram_access_token)
        self._balance_service = BalanceService(telegram_access_token)

        self._lock = threading.Lock()
        self._updates_queue = Queue()

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
            else:
                time.sleep(3)
                continue

            self._update_handler.handle_command(update)

    def start(self):
        handling_thread = threading.Thread(target=self._handle_updates, daemon=True)
        balances_check_thread = threading.Thread(target=self._balance_service.check_balances, daemon=True)

        handling_thread.start()
        balances_check_thread.start()

        self._listen_for_updates()
