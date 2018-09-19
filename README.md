# DeepThought - Artiqox Tipping and Giving Platform.

![Artiqox](https://avatars2.githubusercontent.com/u/37213767?s=250&v=4)
 
#### Artiqox cryptocurrency tipping and giving platform for [Telegram](https://telegram.org) and for [Twitter](http://twitter.com)


## Dependencies 
### Platform

*  `apt-get install python3`
*  `apt-get install python3-pip`
*  `pip3 install beautifulsoup4`

* In order to run the tip-bot effectively, a Bitcoin-core based client is needed. For this git Artiqox Core is used , but any major alternate cryptocurrency client could easily be incorporated.
### Telegram Bot Specific
*  `pip3 install python-telegram-bot --upgrade`
### Twitter Bot Specific
*  `pip3 install tweepy`

## Setup

* Download the git
`git clone https://github.com/artiqox/DeepThought`
### Telegram Bot Setup
* Setup a bot with the user @BotFather through PM on Telegram, after going through a setup you will be given a bot token. Edit the command.py file and on line 13 replace the 'xxxxxxxx' with the bot token you just recieved from @BotFather. 

*  Run the script 
`python3 dttelegram.py`

#### Examples of Commands
*  Initiate the bot by inviting it to a chat or via PM, some commands are `/balance` , `/price` , `/help` and to find out the format related to tip others and withdrawal of funds use `/commands`.

### Twitter Bot Setup

* Setup API tokens for twitter account

* create secrets.py file with content:
`consumer_key = 'xxx' consumer_secret = 'xxx'`
`access_token = 'xxx' access_secret = 'xxx'`

*  Run the script 
`python3 dttwitter.py`

#### Examples of Commands
* tweet with "bot_username @receivingUsername 20" will give @receivingUsername 20 AIQ
* tweet with "bot_username @receivingUsername 20 USD" will give @receivingUsername amount of AIQ that is equal to 20 USD
* tweet that is reply to another tweet (main) with "bot_username 20" will give author of the main tweet 20 AIQ
* tweet with "bot_username balance EUR" will give user balance in EUR
* tweet with "bot_username deposit" will give bot deposit address
* tweet with "bot_username withdraw aaaaaaa 20" will withdraw 20 AIQ to wallet aaaaaaa
* tweet "bot_username help" for more information
---
### Setting up the bot as so still leaves the wallet unencrypted, so please go to extra measures to provide extra security. Make sure to have SSH encryption on whatever device/droplet you run it on. 

*  Please fork the code, happy tipping! 
