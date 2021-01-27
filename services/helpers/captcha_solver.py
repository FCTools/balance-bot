# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of balance-bot project.
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

import os

from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless


class CaptchaSolver:
    def __init__(self):
        self._captcha_api_key = os.getenv("CAPTCHA_SERVICE_KEY")

    def solve(self, data_sitekey, url):
        solver = recaptchaV2Proxyless()
        solver.set_verbose(False)
        solver.set_verbose(1)
        solver.set_key(self._captcha_api_key)
        solver.set_website_url(url)
        solver.set_website_key(data_sitekey)

        return solver.solve_and_return_solution()

