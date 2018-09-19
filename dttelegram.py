# -*- coding: utf-8 -*-

import json
import codecs
import requests
from bs4 import BeautifulSoup, SoupStrainer
import re
import subprocess
from telegram.ext.dispatcher import run_async
from telegram.ext import Updater
from html import escape

updater = Updater(token='xxxxxxxx')
dispatcher = updater.dispatcher

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

def price(bot, update):
	options = update.message.text[7:]
	lowsymb = options.lower()
	uppsymb = options.upper()
	api_url = requests.get('https://api.coingecko.com/api/v3/coins/artiqox?localization=false')
	market_data_json = api_url.json()
	current_price_json = json.loads(json.dumps(market_data_json['market_data']))
	currency_json = json.loads(json.dumps(current_price_json['current_price']))
	if lowsymb in currency_json:
		btc_price = json.dumps(currency_json['btc'])
		symb_price = json.dumps(currency_json[lowsymb])
		last_price = format(float(btc_price), '.8f')
		if lowsymb == 'btc':
			last_fiat = format(float(symb_price), '.8f')
		else:
			last_fiat = format(float(symb_price), '.4f')
		bot.send_message(chat_id=update.message.chat_id, text="Artiqox is valued at {0}฿ ≈ {1}{2}".format(last_price,uppsymb,last_fiat))
	else:
		btc_price = json.dumps(currency_json['btc'])
		usd_price = json.dumps(currency_json['usd'])
		last_price = format(float(btc_price), '.8f')
		last_fiat = format(float(usd_price), '.4f')
		bot.send_message(chat_id=update.message.chat_id, text="Artiqox is valued at {0}฿ ≈ USD{1}".format(last_price,last_fiat))

def example(bot, update):
	user = update.message.from_user.username
	bot.send_message(chat_id=update.message.chat_id, text="Initiating commands /give & /withdraw have a specfic format,\n use them like so:" + "\n \n Parameters: \n <user> = target user to give AIQ \n <amount> = amount of Artiqox to utilise \n <address> = Artiqox address to withdraw to \n \n Giving format: \n /give <user> <amount> \n \n Withdrawing format: \n /withdraw <address> <amount>")

def help(bot, update):
	bot.send_message(chat_id=update.message.chat_id, text="The following commands are at your disposal: /hi , /example , /deposit , /give , /withdraw or /balance")

def deposit(bot, update):
	user = update.message.from_user.username
	options = update.message.text[9:]
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	elif options == "qr":
		address = "/usr/local/bin/artiqox-cli"
		result = subprocess.run([address,"getaccountaddress","TG-" + user.lower()],stdout=subprocess.PIPE)
		clean = (result.stdout.strip()).decode("utf-8")
		bot.send_message(chat_id=update.message.chat_id, text="@{0} your depositing address is: {1}".format(user,clean))
		bot.send_photo(chat_id=update.message.chat_id, photo="https://chart.googleapis.com/chart?cht=qr&chl=artiqox%3A{0}&chs=180x180&choe=UTF-8&chld=L|2".format(clean))
	else:
		address = "/usr/local/bin/artiqox-cli"
		result = subprocess.run([address,"getaccountaddress","TG-" + user.lower()],stdout=subprocess.PIPE)
		clean = (result.stdout.strip()).decode("utf-8")
		bot.send_message(chat_id=update.message.chat_id, text="@{0} your depositing address is: {1}".format(user,clean))

def give(bot,update):
	user = update.message.from_user.username
	target = update.message.text[6:]
	amount =  target.split(" ")[1]
	target =  target.split(" ")[0]
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		machine = "@ArtiqoxBot"
		machine2 = "@username"
		if target.lower() == machine.lower():
			bot.send_message(chat_id=update.message.chat_id, text="This ain't Free Parking. HODL.")
		elif target.lower() == machine2.lower():
			bot.send_message(chat_id=update.message.chat_id, text="I don't think @username is too fussy about receiving some AIQ. Let's HODL.")
		elif "@" in target:
			target = target[1:]
			user = update.message.from_user.username
			core = "/usr/local/bin/artiqox-cli"
			result = subprocess.run([core,"getbalance","TG-" + user.lower()],stdout=subprocess.PIPE)
			balance = float((result.stdout.strip()).decode("utf-8"))
			amount = float(amount)
			if balance < amount:
				bot.send_message(chat_id=update.message.chat_id, text="@{0} you have insufficent funds.".format(user))
			elif target == user:
				bot.send_message(chat_id=update.message.chat_id, text="You can't give yourself AIQ.")
			elif len(target) < 5:
				bot.send_message(chat_id=update.message.chat_id, text="Error that user is not applicable. Telegram requires users to have 5 or more characters in their @username.")
			else:
				balance = str(balance)
				amount = str(amount)
				tx = subprocess.run([core,"move","TG-" + user.lower(),"TG-" + target.lower(),amount],stdout=subprocess.PIPE)
				bot.send_message(chat_id=update.message.chat_id, text="Hey @{1}, @{0} gave you {2} AIQ".format(user, target, amount))
		else:
			bot.send_message(chat_id=update.message.chat_id, text="Error that user is not applicable.")

def balance(bot,update):
	user = update.message.from_user.username
	options = update.message.text[9:]
	lowsymb = options.lower()
	uppsymb = options.upper()
	api_url = requests.get('https://api.coingecko.com/api/v3/coins/artiqox?localization=false')
	market_data_json = api_url.json()
	current_price_json = json.loads(json.dumps(market_data_json['market_data']))
	currency_json = json.loads(json.dumps(current_price_json['current_price']))
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		if lowsymb in currency_json:
			fiat_price = json.dumps(currency_json[lowsymb])
			if lowsymb == 'btc':
				decplace = 8
			else:
				decplace = 4
		else:
			fiat_price = json.dumps(currency_json['usd'])
			uppsymb = "USD"
			decplace = 4
		core = "/usr/local/bin/artiqox-cli"
		result = subprocess.run([core,"getbalance","TG-" + user.lower()],stdout=subprocess.PIPE)
		clean = (result.stdout.strip()).decode("utf-8")
		balance  = float(clean)
		last_fiat = float(fiat_price)
		fiat_balance = balance * last_fiat
		fiat_balance = str(round(fiat_balance,decplace))
		balance =  str(round(balance,4))
		bot.send_message(chat_id=update.message.chat_id, text="@{0} your current balance is: {1} AIQ ≈ {2}{3}".format(user,balance,uppsymb,fiat_balance))

def withdraw(bot,update):
	user = update.message.from_user.username
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		target = update.message.text[9:]
		address = target[:35]
		address = ''.join(str(e) for e in address)
		target = target.replace(target[:35], '')
		amount = float(target)
		core = "/usr/local/bin/artiqox-cli"
		result = subprocess.run([core,"getbalance","TG-" + user.lower()],stdout=subprocess.PIPE)
		clean = (result.stdout.strip()).decode("utf-8")
		balance = float(clean)
		if balance < amount:
			bot.send_message(chat_id=update.message.chat_id, text="@{0} you have insufficent funds.".format(user))
		else:
			amount = str(amount)
			tx = subprocess.run([core,"sendfrom","TG-" + user.lower(),address,amount],stdout=subprocess.PIPE)
			bot.send_message(chat_id=update.message.chat_id, text="@{0} has successfully withdrew to address: {1} of {2} AIQ" .format(user,address,amount))

def hi(bot,update):
	user = update.message.from_user.username
	bot.send_message(chat_id=update.message.chat_id, text="Hello @{0}, how are you doing today?".format(user))

def moon(bot,update):
	bot.send_message(chat_id=update.message.chat_id, text="Rocket to the moon is taking off!")

def tip(bot,update):
	user = update.message.from_user.username
	target = update.message.text[5:]
	amount =  target.split(" ")[1]
	target =  target.split(" ")[0]
	bot.send_message(chat_id=update.message.chat_id, text="¯\_(ツ)_/¯ Maybe try /give {0} {1}".format(target,amount))  

from telegram.ext import CommandHandler

price_handler = CommandHandler('price', price)
dispatcher.add_handler(price_handler)

example_handler = CommandHandler('example', example)
dispatcher.add_handler(example_handler)

moon_handler = CommandHandler('moon', moon)
dispatcher.add_handler(moon_handler)

hi_handler = CommandHandler('hi', hi)
dispatcher.add_handler(hi_handler)

withdraw_handler = CommandHandler('withdraw', withdraw)
dispatcher.add_handler(withdraw_handler)

deposit_handler = CommandHandler('deposit', deposit)
dispatcher.add_handler(deposit_handler)

give_handler = CommandHandler('give', give)
dispatcher.add_handler(give_handler)

tip_handler = CommandHandler('tip', tip)
dispatcher.add_handler(tip_handler)

balance_handler = CommandHandler('balance', balance)
dispatcher.add_handler(balance_handler)

commands_handler = CommandHandler('commands', help)
dispatcher.add_handler(commands_handler)

help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)

updater.start_polling()
