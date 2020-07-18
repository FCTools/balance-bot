# balance-bot
Telegram bot for balances control.

## Available options

### Commands
1. `/start` - greeting
2. `/help` - help message
3. `/get_balance [network_alias]`

   Returns balance for selected network. If [network] is empty, returns balances for all available networks. 
   
   Example: `/get_balance prop`
4. `/set_info_balance [network alias] [balance]`

   Sets balance (border) for info-level and selected network. 
   
   Example: `/set_info_balance eva 150`
5. `/set_warning_balance [network alias] [balance]`
   Sets balance (border) for warning-level and selected network. 
   
   Example: `/set_warning_balance pushhouse 70`
5. `/set_critical_balance [network alias] [balance]`
   
   Sets balance (border) for critical-level and selected network. 
   
   Example: `/set_critical_balance prop 40`

### Available networks
1. Propeller Ads (alias - prop)
2. Push.house (alias - pushhouse)
3. Evadav (alias - eva)

Basicly, bot checks balances every 15 munites. If balance is less than some border (e.g. info-border), bot sends notification every 2 hours to all users from database. Then, if level has changed (e.g. balance moved from warning-zone to critical-zone), bot sends notification to all users immidiately.
