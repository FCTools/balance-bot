# Balance bot
<p align="center">
<a href="https://t.me/alcatraz_rm"><img src="https://img.shields.io/badge/Telegram Chat-@alcatraz_rm-2CA5E0.svg?logo=telegram&style=for-the-badge" alt="Chat on Telegram"/></a>
<img src="https://img.shields.io/badge/version-v.1.0.0.stable.77-green?style=for-the-badge" alt="Last Release"/>
</p>
Telegram bot for traffic sources balances control.

Project name for copyright: balance-bot

## Available options

### Commands
1. `/start` - greeting
2. `/help` - help message
3. `/get_balance [network_alias]`

   Returns balance for a selected network. If `[network_alias]` is empty, returns balances for all available networks. 
   
   Example: `/get_balance prop`
   
4. `/set_info_balance [network alias] [balance]`

   Sets balance (border) for info-level and selected network. 
   
   Example: `/set_info_balance eva 150`
   
5. `/set_warning_balance [network alias] [balance]`
   Sets balance (border) for warning-level and selected network. 
   
   Example: `/set_warning_balance pushhouse 70`
   
6. `/set_critical_balance [network alias] [balance]`
   
   Sets balance (border) for critical-level and selected network. 
   
   Example: `/set_critical_balance prop 40`
   
7. `/set_notifications_interval [interval in hours]`
    
    Sets notifications interval. Notification interval must be more than 20.4 minutes (0.34 hours) and less than 6 hours.
    
    Example: `/set_notifications_interval 2.5`
8. `/disable [network alias]`
   
    Disables notifications for given network.

9. `/enable [network alias]`

    Enables notifications for given network.

### Available networks
1. Propeller Ads (alias - `prop`) - via [api](https://ssp-api.propellerads.com/v5/docs/#/)
2. Push.house (alias - `pushhouse`) - via web-interface
3. Evadav (alias - `eva`) - via [api](https://evadav.com/docs/api)
4. DaoPush (alias - `dao`) - via web-interface
5. ZeroPark (alias - `zero`) - via [api](https://panel.zeropark.com/secure/apidocs/apiguide.pdf)
6. MGID (alias - `mgid`) - via [api](https://help.mgid.com/ru/rest-api-mgid-advertisers)

Basically, bot checks balances every 20 minutes. If balance is less than some border (e.g. info-border), bot sends notification every 2 hours to all users from database. Then, if level has changed (e.g. balance moved from warning-zone to critical-zone), bot sends notification to all users immediately.

Stack:
* [requests](https://requests.readthedocs.io/en/master/) library for http-requests
* [Sqlite3](https://pypi.org/project/redis/) as database
* [AntiCaptcha service](https://anti-captcha.com) and 
  [official library](https://github.com/AdminAnticaptcha/anticaptcha-python) for CAPTCHA solving

<br>
<br>
<p align="center">
Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
</p>

