import os

from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless


class CaptchaSolver:
    def __init__(self):
        self._captcha_api_key = os.getenv("CAPTCHA_SERVICE_KEY")

    def solve(self, data_sitekey, url):
        solver = recaptchaV2Proxyless()
        # solver.set_verbose(False) - you can do this for disable console logging
        solver.set_verbose(1)
        solver.set_key(self._captcha_api_key)
        solver.set_website_url(url)
        solver.set_website_key(data_sitekey)

        return solver.solve_and_return_solution()

