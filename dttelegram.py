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

import sys
import sqlite3
import re
from datetime import datetime, timedelta
#from secrets import *
from hashids import Hashids
import string
from random import *
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import tweepy

from secrets import *



auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

updater = Updater(token=telegram_token)
dispatcher = updater.dispatcher
core = "/home/debian/artiqox-node/artiqox-cli"
address = core
sqlite_file = '/home/debian/giveaiq/app.db'


import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

def get_voucher_number(id):
	hash_id = Hashids(salt=vouchers_salt, min_length=8)
	return hash_id.encode(id)

def get_voucher_id(voucher_number):
	hash_id = Hashids(salt=vouchers_salt, min_length=8)
	return hash_id.decode(voucher_number)[0]

def get_user_id(user_name):
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	cmd = "select id from user where username = '{0}'".format(user_name)
	user_id = c.execute(cmd, ).fetchone()[0]
	conn.close()
	return user_id

def get_status_id(status_name):
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	cmd = "select id from giveaiq_status where name = '{0}'".format(status_name)
	status_id = c.execute(cmd, ).fetchone()[0]
	conn.close()
	return status_id

def get_notify_me(giveaiq_user_name):
	giveaiq_displayname = giveaiq_user_name[3:]
	giveaiq_accounttype = giveaiq_user_name[0:3] 
	print(giveaiq_user_name)
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	if giveaiq_accounttype == "TG-":
		cmd = "select notify_me from usertelegram where name = '{0}'".format(giveaiq_displayname)
	elif giveaiq_accounttype == "TW-":
		cmd = "select notify_me from usertwitter where screen_name = '{0}'".format(giveaiq_displayname)
	notify_me = c.execute(cmd, ).fetchone()
	if notify_me:
		notify_me = notify_me[0]
	else:
		notify_me = 0
	conn.close()
	return notify_me

def change_user_tweet(user):
	allchar = string.ascii_letters + string.digits
	catchy = "".join(choice(allchar) for x in range(randint(5, 5)))
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	cmd = "UPDATE user SET confirm_my_stuff=? where username=?"
	c.execute(cmd, (catchy, user))
	conn.commit()
	conn.close()

def get_balance(giveaiq_user_name):
    giveaiq_displayname = giveaiq_user_name[3:]
    giveaiq_accounttype = giveaiq_user_name[0:3]    
    result = subprocess.run([core,"getbalance",giveaiq_accounttype + giveaiq_displayname.lower()],stdout=subprocess.PIPE)
    clean = (result.stdout.strip()).decode("utf-8")
    return float(clean)

def update_usertelegram(user):
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	cmd = "INSERT OR IGNORE INTO usertelegram (name) VALUES (?)"
	c.execute(cmd, (user, ))
	conn.commit()
	conn.close()

def update_usertwitter(user):
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    cmd = "INSERT OR IGNORE INTO usertwitter (screen_name) VALUES (?)"
    c.execute(cmd, (user, ))
    conn.commit()
    conn.close()

def update_tweet(tweet_id, conn):
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    status = api.get_status(tweet_id, tweet_mode='extended')
    print(status)
    tweet_author_id = status.user.id
    tweet_author_screen_name = status.user.screen_name
    tweet_author_name = status.user.name
    tweet_author_description = status.user.description
    tweet_author_location = status.user.location
    tweet_author_url = status.user.url
    tweet_author_followers_count = status.user.followers_count
    tweet_author_friends_count = status.user.friends_count
    tweet_author_created_at = status.user.created_at
    tweet_full_text = status.full_text
    tweet_in_reply_to_status_id = status.in_reply_to_status_id
    tweet_in_reply_to_user_id = status.in_reply_to_user_id
    tweet_in_reply_to_screen_name = status.in_reply_to_screen_name
    tweet_geo = status.geo
    tweet_coordinates = status.coordinates
    tweet_place = status.place
    tweet_created_at = status.created_at
    tweet_contributors = status.contributors
    tweet_retweet_count = status.retweet_count
    tweet_favorite_count = status.favorite_count
    tweet_possibly_sensitive = ""
    tweet_lang = status.lang
    cmd = "INSERT OR IGNORE INTO usertwitter (screen_name) VALUES (?)"
    c.execute(cmd, (tweet_author_screen_name, ))
    if tweet_in_reply_to_screen_name:
        cmd = "INSERT OR IGNORE INTO usertwitter (screen_name) VALUES (?)"
        c.execute(cmd, (tweet_in_reply_to_screen_name))
    cmd = "UPDATE usertwitter SET name=?, location=?, description=?, url=?, followers_count=?, friends_count=? WHERE screen_name=?"
    c.execute(cmd, (tweet_author_name, tweet_author_location, tweet_author_description, tweet_author_url, tweet_author_followers_count, tweet_author_friends_count, tweet_author_screen_name))
    cmd = "INSERT OR IGNORE INTO twitter_tweet (id, added_date) VALUES (?, ?)"
    c.execute(cmd, (tweet_id, datetime.utcnow(), ))
    cmd = "UPDATE twitter_tweet SET full_text=?, usertwitter_screen_name=?, in_reply_to_status_id=?, in_reply_to_screen_name=?, possibly_sensitive=? WHERE id=?"
    c.execute(cmd, (tweet_full_text, tweet_author_screen_name, tweet_in_reply_to_status_id, tweet_in_reply_to_screen_name, tweet_possibly_sensitive, tweet_id))
    conn.commit()
#    conn.close()

def telegram_giver(giveaiq_user_name, giveaiq_user_name_target, amount_aiq, in_reply_to_status_id_str):
	giveaiq_displayname = giveaiq_user_name[3:]
	giveaiq_accounttype = giveaiq_user_name[0:3]
	giveaiq_displayname_target = giveaiq_user_name_target[3:]
	giveaiq_accounttype_target = giveaiq_user_name_target[0:3] 
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	if in_reply_to_status_id_str:

		tx = subprocess.run([core,"move",giveaiq_accounttype + giveaiq_displayname.lower(),giveaiq_accounttype_target + giveaiq_displayname_target.lower(),amount_aiq, "1", str(in_reply_to_status_id_str)],stdout=subprocess.PIPE)
		cmd = "UPDATE twitter_tweet SET total_received_amount = total_received_amount + ?, total_received_number = total_received_number + 1 WHERE id=?"
		c.execute(cmd, (amount_aiq, in_reply_to_status_id_str, ))
		cmd = "UPDATE usertwitter SET total_received_amount = total_received_amount + ?, total_received_number = total_received_number + 1 WHERE screen_name=?"
		c.execute(cmd, (amount_aiq, giveaiq_displayname_target, ))
		cmd = "UPDATE usertelegram SET total_gives_amount = total_gives_amount + ?, total_gives_number = total_gives_number + 1 WHERE screen_name=?"
		c.execute(cmd, (amount_aiq, giveaiq_displayname, ))
		conn.commit()
	else:
		tx = subprocess.run([core,"move",giveaiq_accounttype + giveaiq_displayname.lower(),giveaiq_accounttype_target + giveaiq_displayname_target.lower(),amount_aiq],stdout=subprocess.PIPE)
		if giveaiq_accounttype_target == "TG-":
			cmd = "UPDATE usertelegram SET total_received_amount = total_received_amount + ?, total_received_number = total_received_number + 1 WHERE name=?"
		elif giveaiq_accounttype_target == "TW-":
			cmd = "UPDATE usertwitter SET total_received_amount = total_received_amount + ?, total_received_number = total_received_number + 1 WHERE screen_name=?"
		c.execute(cmd, (amount_aiq, giveaiq_displayname_target, ))
		cmd = "UPDATE usertelegram SET total_gives_amount = total_gives_amount + ?, total_gives_number = total_gives_number + 1 WHERE name=?"
		c.execute(cmd, (amount_aiq, giveaiq_displayname, ))
		conn.commit()
	conn.close()

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
		bot.send_message(chat_id=update.message.chat_id, text="Artiqox is valued at {0} ≈ {1}{2}".format(last_price,uppsymb,last_fiat))
	else:
		btc_price = json.dumps(currency_json['btc'])
		usd_price = json.dumps(currency_json['usd'])
		last_price = format(float(btc_price), '.8f')
		last_fiat = format(float(usd_price), '.4f')
		bot.send_message(chat_id=update.message.chat_id, text="Artiqox is valued at {0} ≈ USD{1}".format(last_price,last_fiat))

def example(bot, update):
	user = update.message.from_user.username
	bot.send_message(chat_id=update.message.chat_id, text="Initiating commands /give & /withdraw have a specfic format,\n use them like so:" + "\n \n Parameters: \n <user> = target user to give AIQ \n <amount> = amount of Artiqox to utilise \n <address> = Artiqox address to withdraw to \n \n Giving format: \n /give <user> <amount> \n \n Withdrawing format: \n /withdraw <address> <amount>")

def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="The following commands are at your disposal: /hi , /example , /deposit , /give , /give2twitter, /cryptorain, /withdraw or /balance\nvisit https://giveaiq.online")

def deposit(bot, update):
	user = update.message.from_user.username
	options = update.message.text[9:]
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	elif options == "qr":
		result = subprocess.run([address,"getaccountaddress","TG-" + user.lower()],stdout=subprocess.PIPE)
		clean = (result.stdout.strip()).decode("utf-8")
		bot.send_message(chat_id=update.message.chat_id, text="@{0} your depositing address is: {1}".format(user,clean))
		bot.send_photo(chat_id=update.message.chat_id, photo="https://chart.googleapis.com/chart?cht=qr&chl=artiqox%3A{0}&chs=180x180&choe=UTF-8&chld=L|2".format(clean))
	else:
		result = subprocess.run([address,"getaccountaddress","TG-" + user.lower()],stdout=subprocess.PIPE)
		clean = (result.stdout.strip()).decode("utf-8")
		bot.send_message(chat_id=update.message.chat_id, text="@{0} your depositing address is: {1}".format(user,clean))

def give(bot,update):
	user = update.message.from_user.username
	target = update.message.text[6:]
	amount =  target.split(" ")[1]
	if target.count(" ") > 1:
		options =  target.split(" ")[2]
	else:
		options = "AIQ"
	target =  target.split(" ")[0]
	
	if "@" in target:
		target2 = target[1:]
	giveaiq_user_name = "TG-"+user
	giveaiq_user_name_target = "TG-"+target2
	update_usertelegram(giveaiq_user_name[3:])
	update_usertelegram(giveaiq_user_name_target[3:])
	if get_notify_me(giveaiq_user_name_target) == 1:
		target_notify_me="@"+target2
	else:
		target_notify_me=target2
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		machine = "@ArtiqoxBot"
		machine2 = "@username"
		if target.lower() == machine.lower():
			bot.send_message(chat_id=update.message.chat_id, text="This ain't Free Parking. HODL.")
		elif target.lower() == machine2.lower():
			bot.send_message(chat_id=update.message.chat_id, text="I don't think @username is too fussy about receiving some AIQ. Let's HODL.")
		elif target2:
			lowsymb = options.lower()
			uppsymb = options.upper()
			api_url = requests.get('https://api.coingecko.com/api/v3/coins/artiqox?localization=false')
			market_data_json = api_url.json()
			current_price_json = json.loads(json.dumps(market_data_json['market_data']))
			currency_json = json.loads(json.dumps(current_price_json['current_price']))
			
			balance = get_balance(giveaiq_user_name)
			if lowsymb in currency_json:
				fiat_price = json.dumps(currency_json[lowsymb])
				if lowsymb == 'btc' or lowsymb == 'aiq':
					decplace = 8
				else:
					decplace = 8
			else:
				fiat_price = 1.0
				uppsymb = "AIQ"
				decplace = 8
			
			last_fiat = float(fiat_price)
			fiat_balance = balance * last_fiat
			fiat_balance = str(round(fiat_balance,decplace))
			amount = float(amount)
			amount_aiq = amount / last_fiat
			amount_aiq = float(amount_aiq) 

			if balance < amount_aiq:
				bot.send_message(chat_id=update.message.chat_id, text="@{0} you have insufficent funds.".format(user))
			elif target2 == user:
				bot.send_message(chat_id=update.message.chat_id, text="You can't give yourself AIQ.")
			elif len(target2) < 5:
				bot.send_message(chat_id=update.message.chat_id, text="Error that user is not applicable. Telegram requires users to have 5 or more characters in their @username.")
			elif uppsymb == "AIQ":
				balance = str(balance)
				amount = str(amount)
				amount_aiq = str(round(amount_aiq,decplace))
				telegram_giver(giveaiq_user_name, giveaiq_user_name_target, amount_aiq, "")
				amount_aiq = '{0:.8f}'.format(float(amount_aiq))
				bot.send_message(chat_id=update.message.chat_id, text="Hey {1}, @{0} gave you {2} AIQ".format(user, target_notify_me, amount))
			else:
				balance = str(balance)
				amount = str(amount)
				amount_aiq = str(round(amount_aiq,decplace))
				telegram_giver(giveaiq_user_name, giveaiq_user_name_target, amount_aiq, "")
				amount_aiq = '{0:.8f}'.format(float(amount_aiq))
				amount = '{0:.8f}'.format(float(amount))
				bot.send_message(chat_id=update.message.chat_id, text="Hey {1}, @{0} gave you {2} AIQ ≈ {3}{4}.".format(user, target_notify_me, amount_aiq, uppsymb, amount))
		else:
			bot.send_message(chat_id=update.message.chat_id, text="Error that user is not applicable.")

def give2twitter(bot,update):
	user = update.message.from_user.username
	target = update.message.text[14:]
	amount =  target.split(" ")[1]
	if target.count(" ") > 1:
		options =  target.split(" ")[2]
	else:
		options = "AIQ"
	target =  target.split(" ")[0]
	
	if "@" in target:
		target2 = target[1:]
	giveaiq_user_name = "TG-"+user
	giveaiq_user_name_target = "TW-"+target2
	update_usertelegram(giveaiq_user_name[3:])
	update_usertwitter(giveaiq_user_name_target[3:])
	if get_notify_me(giveaiq_user_name_target) == 1:
		target_notify_me="@"+target2
	else:
		target_notify_me=target2
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		machine = "@GiveAIQ"
		machine2 = "@username"
		if target.lower() == machine.lower():
			bot.send_message(chat_id=update.message.chat_id, text="This ain't Free Parking. HODL.")
		elif target.lower() == machine2.lower():
			bot.send_message(chat_id=update.message.chat_id, text="I don't think @username is too fussy about receiving some AIQ. Let's HODL.")
		elif target2:
			lowsymb = options.lower()
			uppsymb = options.upper()
			api_url = requests.get('https://api.coingecko.com/api/v3/coins/artiqox?localization=false')
			market_data_json = api_url.json()
			current_price_json = json.loads(json.dumps(market_data_json['market_data']))
			currency_json = json.loads(json.dumps(current_price_json['current_price']))
			
			balance = get_balance(giveaiq_user_name)
			if lowsymb in currency_json:
				fiat_price = json.dumps(currency_json[lowsymb])
				if lowsymb == 'btc' or lowsymb == 'aiq':
					decplace = 8
				else:
					decplace = 8
			else:
				fiat_price = 1.0
				uppsymb = "AIQ"
				decplace = 8
			
			last_fiat = float(fiat_price)
			fiat_balance = balance * last_fiat
			fiat_balance = str(round(fiat_balance,decplace))
			amount = float(amount)
			amount_aiq = amount / last_fiat
			amount_aiq = float(amount_aiq) 

			if balance < amount_aiq:
				bot.send_message(chat_id=update.message.chat_id, text="@{0} you have insufficent funds.".format(user))
			elif uppsymb == "AIQ":
				balance = str(balance)
				amount = str(amount)
				amount_aiq = str(round(amount_aiq,decplace))
				telegram_giver(giveaiq_user_name, giveaiq_user_name_target, amount_aiq, "")
				amount_aiq = '{0:.8f}'.format(float(amount_aiq))
				bot.send_message(chat_id=update.message.chat_id, text="Hey @{0}, I transfered {2} AIQ to twitter user {1}".format(user, target_notify_me, amount))
			else:
				balance = str(balance)
				amount = str(amount)
				amount_aiq = str(round(amount_aiq,decplace))
				telegram_giver(giveaiq_user_name, giveaiq_user_name_target, amount_aiq, "")
				amount_aiq = '{0:.8f}'.format(float(amount_aiq))
				amount = '{0:.8f}'.format(float(amount))
				bot.send_message(chat_id=update.message.chat_id, text="Hey @{0}, I transfered {2} AIQ ≈ {3}{4} to twitter user {1}.".format(user, target_notify_me, amount_aiq, uppsymb, amount))
		else:
			bot.send_message(chat_id=update.message.chat_id, text="Error that user is not applicable.")

def verification(bot,update):
	user = update.message.from_user.username
	user_message = update.message.text[10:]
	tweettext =  user_message.split(" ")[0]
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	giveaiq_user_name = "TG-"+user
	cmd = "SELECT password_hash, confirm_my_stuff FROM verification WHERE username=?"
	c.execute(cmd, (giveaiq_user_name, ))
	hash_exists = c.fetchall()

	if hash_exists:
		for worder in hash_exists:
			password_hash = worder[0]
			confirm_my_stuff = worder[1]
			if tweettext == confirm_my_stuff:
				cmd = "INSERT OR IGNORE INTO user (username, displayname, password_hash) VALUES (?, ?, ?)"
				c.execute(cmd, (giveaiq_user_name, user, password_hash))
				conn.commit()
				cmd = "UPDATE user SET password_hash=? where username=?"
				c.execute(cmd, (password_hash, giveaiq_user_name))
				conn.commit()
				cmd = "INSERT OR IGNORE INTO usertelegram (name) VALUES (?)"
				c.execute(cmd, (user, ))
				conn.commit()
				change_user_tweet(giveaiq_user_name)
				cmd = "DELETE FROM verification WHERE username=?"
				c.execute(cmd, (giveaiq_user_name, ))
				conn.commit()
				bot.send_message(chat_id=update.message.chat_id, text="Hey @{0}, your GiveAIQ account is verified now.".format(user))
	conn.close()

def withdraw_orders(bot,update):
	user = update.message.from_user.username
	user_message = update.message.text[17:]
	tweettext =  user_message.split(" ")[0]
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	giveaiq_user_name = "TG-"+user
	cmd = "SELECT id, target_wallet, amount FROM withdraw WHERE user_id=? and status=(select id from giveaiq_status where name=\"Withdraw Awaiting Confirmation\")"
	c.execute(cmd, (get_user_id(giveaiq_user_name), ))
	withdraws_hash = c.fetchall()
	cmd = "SELECT id, confirm_my_stuff FROM user WHERE username=?"
	c.execute(cmd , (giveaiq_user_name, ))
	id_confirm_my_stuff = c.fetchone()
	if withdraws_hash and id_confirm_my_stuff and tweettext == id_confirm_my_stuff[1]:
		giveaiq_user_id = id_confirm_my_stuff[0]
		current_time = datetime.utcnow()
		for worder in withdraws_hash:
			id= worder[0]
			address = ''.join(str(e) for e in worder[1])
			amount = float(worder[2])
			balance = get_balance(giveaiq_user_name)
			print(id)
			print(address)
			print(amount)
			print(balance)
			if balance < amount:
				cmd = "UPDATE withdraw SET status=(select id from giveaiq_status where name=\"Withdraw Cancelled\"), comment=\"Cancelled by telegram bot due to no funds\" WHERE id=?"
				c.execute(cmd, (id, ))
			else:
				amount = str(amount)
				tx = subprocess.run([core,"sendfrom","TG-" + user.lower(),address,amount],stdout=subprocess.PIPE)
				cmd = "UPDATE withdraw SET status=(select id from giveaiq_status where name=\"Withdraw Executed\"), comment=\"Executed by telegram bot\" WHERE id=?"
				c.execute(cmd, (id, ))
			conn.commit()
		change_user_tweet(giveaiq_user_name)
		bot.send_message(chat_id=update.message.chat_id, text="Hey @{0}, your withdraws were executed.".format(user))
	conn.close()

def voucher_orders(bot,update):
	user = update.message.from_user.username
	user_message = update.message.text[16:]
	tweettext =  user_message.split(" ")[0]
	
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	giveaiq_accounttype="TG-"
	giveaiq_user_name = "TG-"+user
	
	cmd = "SELECT id, amount FROM voucher WHERE user_id=? and status=(select id from giveaiq_status where name=\"Voucher Awaiting Confirmation\")"
	c.execute(cmd, (get_user_id(giveaiq_user_name), ))
	vouchers_hash = c.fetchall()

	cmd = "SELECT id, confirm_my_stuff FROM user WHERE username=?"
	c.execute(cmd , (giveaiq_user_name, ))
	id_confirm_my_stuff = c.fetchone()
	
	if vouchers_hash and id_confirm_my_stuff and tweettext == id_confirm_my_stuff[1]:
		giveaiq_user_id = id_confirm_my_stuff[0]
		current_time = datetime.utcnow()
		for worder in vouchers_hash:
			id=worder[0]
			voucher_number=get_voucher_number(id)
			amount=float(worder[1])
			balance = get_balance(giveaiq_user_name)
	
			if balance < amount:
				cmd = "UPDATE voucher SET status=(select id from giveaiq_status where name=\"Voucher Cancelled\"), comment=\"Cancelled by twitter bot due to no funds\" WHERE id=?"
				c.execute(cmd, (id, ))
			else:
				amount = str(amount)
				tx = subprocess.run([core,"move",giveaiq_accounttype + user.lower(),"VOUCHER-" + voucher_number,amount],stdout=subprocess.PIPE)
				cmd = "UPDATE voucher SET status=(select id from giveaiq_status where name=\"Voucher Active\"), comment=\"Activated by twitter bot\" WHERE id=?"
				c.execute(cmd, (id, ))
			conn.commit()
		bot.send_message(chat_id=update.message.chat_id, text="Hey @{0}, your vouchers were created.".format(user))
	change_user_tweet(giveaiq_user_name)
	
	conn.close()

def promotedtweet_orders(bot,update):
	user = update.message.from_user.username
	user_message = update.message.text[16:]
	tweettext =  user_message.split(" ")[0]
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	giveaiq_user_name = "TG-"+user
	cmd = "SELECT promoted_tweet.id, tweet_category.price, promoted_tweet.tweet_id FROM promoted_tweet, tweet_category WHERE promoted_tweet.cat_id=tweet_category.id and promoted_tweet.user_id=? and promoted_tweet.status=?"
	c.execute(cmd, (get_user_id(giveaiq_user_name), get_status_id("Tweet Awaiting Confirmation"), ))
	promoted_tweets_hash = c.fetchall()

	cmd = "SELECT id, confirm_my_stuff FROM user WHERE username=?"
	c.execute(cmd , (giveaiq_user_name, ))
	id_confirm_my_stuff = c.fetchone()
	if promoted_tweets_hash and id_confirm_my_stuff and tweettext == id_confirm_my_stuff[1]:
		giveaiq_user_id = id_confirm_my_stuff[0]
		current_time = datetime.utcnow()
		one_day_ahead = current_time + timedelta(days=1)
		for worder in promoted_tweets_hash:
			id = worder[0]
			if worder[1]:
				amount = float(worder[1])
			else:
				amount = 0.0
			tweet_id = worder[2]
			update_tweet(tweet_id, conn)
			cmd = "SELECT notify_me, promote_me FROM usertwitter WHERE screen_name=(select usertwitter_screen_name from twitter_tweet where id=?)"
			c.execute(cmd , (tweet_id, ))
			promote_me = c.fetchone()[1]
			balance = get_balance(giveaiq_user_name)
			if balance < amount:
				cmd = "UPDATE promoted_tweet set status=(select id from giveaiq_status where name=\"Not enough funds, Promote Tweet order cancelled\") WHERE id=?"
				c.execute(cmd, (id, ))
			elif promote_me != 1:
				cmd = "UPDATE promoted_tweet set status=(select id from giveaiq_status where name=\"Author of the tweet does not allow promoting it\") WHERE id=?"
				c.execute(cmd, (id, ))
			else:
				amount = str(amount)
				
				if amount != "0.0":
					tx = subprocess.run([core,"sendfrom","TG-" + user.lower(),earning_address,amount],stdout=subprocess.PIPE)
				cmd = "UPDATE promoted_tweet set status=(select id from giveaiq_status where name=\"Promote Tweet Order Paid\"), activated_date=?, validtill_date=? WHERE id=?"
				c.execute(cmd, (current_time, one_day_ahead, id))
			conn.commit()
		change_user_tweet(giveaiq_user_name)
		bot.send_message(chat_id=update.message.chat_id, text="Hey @{0}, your tweets are now promoted.".format(user))
	conn.close()

def cryptorain(bot,update):
	user = update.message.from_user.username
	user_message = update.message.text[12:]
	amount = user_message.split(" ")[0]
	options = user_message.split(" ")[1]
	receivers = user_message
	giveaiq_user_name = "TG-"+user
	receivers_list = [word for word in receivers.split() if word.startswith('@')]
	if options:
		lowsymb = options.lower()
		uppsymb = options.upper()
	else:
		lowsymb = "aiq"
		uppsymb = "AIQ"
	api_url = requests.get('https://api.coingecko.com/api/v3/coins/artiqox?localization=false')
	market_data_json = api_url.json()
	current_price_json = json.loads(json.dumps(market_data_json['market_data']))
	currency_json = json.loads(json.dumps(current_price_json['current_price']))
	received_list = ""
	for receiver in receivers_list:
	
		if get_notify_me("TG-"+receiver[1:]) == 1:
			target_notify_me=receiver
		else:
			target_notify_me=receiver[1:]
	
		target = receiver[1:]
		if lowsymb in currency_json:
			fiat_price = json.dumps(currency_json[lowsymb])
			if lowsymb == 'btc' or lowsymb == 'aiq':
				decplace = 8
			else:
				decplace = 8
		else:
			fiat_price = 1.0
			uppsymb = "AIQ"
			decplace = 8
		last_fiat = float(fiat_price)
		
		balance = get_balance(giveaiq_user_name)
		fiat_balance = balance * last_fiat
		fiat_balance = str(round(fiat_balance,decplace))
		amount = float(amount)
		amount_aiq = amount / last_fiat
		amount_aiq = float(amount_aiq)   
		if balance < amount_aiq:
			print("hacker trying to rain more than he has?")
		elif target == user:
			print("dummy hacker trying to gie to himself:)")
		elif uppsymb == "AIQ":
			balance = str(balance)
			amount = str(amount)
			amount_aiq = str(round(amount_aiq,decplace))
			tx = subprocess.run([core,"move","TG-" + user.lower(),"TG-" + target.lower(),amount_aiq],stdout=subprocess.PIPE)
			amount_aiq = '{0:.8f}'.format(float(amount_aiq))
			received_list = received_list+" "+target_notify_me
		else:
			balance = str(balance)
			amount = str(amount)
			amount_aiq = str(round(amount_aiq,decplace))
			tx = subprocess.run([core,"move","TG-" + user.lower(),"TG-" + target.lower(),amount_aiq],stdout=subprocess.PIPE)
			amount_aiq = '{0:.8f}'.format(float(amount_aiq))
			amount = '{0:.8f}'.format(float(amount))
			received_list = received_list+" "+target_notify_me
	if uppsymb == "AIQ" and len(received_list) >= 1:
		bot.send_message(chat_id=update.message.chat_id, text="Hi{1} your friend @{0} #cryptorain you with {2} AIQ.".format(user, received_list, amount_aiq, uppsymb, amount))
		
	elif len(received_list) >= 1:
		bot.send_message(chat_id=update.message.chat_id, text="Hi{1} your friend @{0} #cryptorain you with {2} AIQ ≈ {3}{4}.".format(user, received_list, amount_aiq, uppsymb, amount))

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
	bot.send_message(chat_id=update.message.chat_id, text="Hello @{0}, how are you doing today?\nvisit https://giveaiq.online".format(user))

def moon(bot,update):
	bot.send_message(chat_id=update.message.chat_id, text="Rocket to the moon is taking off!")

def tip(bot,update):
	user = update.message.from_user.username
	target = update.message.text[5:]
	amount =  target.split(" ")[1]
	target =  target.split(" ")[0]
	bot.send_message(chat_id=update.message.chat_id, text="\_(?)_/ Maybe try /give {0} {1}".format(target,amount))  

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

give2twitter_handler = CommandHandler('give2twitter', give2twitter)
dispatcher.add_handler(give2twitter_handler)

verifyme_handler = CommandHandler('verifyme', verification)
dispatcher.add_handler(verifyme_handler)

promotemystuff_handler = CommandHandler('promotemystuff', promotedtweet_orders)
dispatcher.add_handler(promotemystuff_handler)

withdrawmystuff_handler = CommandHandler('withdrawmystuff', withdraw_orders)
dispatcher.add_handler(withdrawmystuff_handler)

crytpovouchers_handler = CommandHandler('cryptovouchers', voucher_orders)
dispatcher.add_handler(crytpovouchers_handler)

cryptorain_handler = CommandHandler('cryptorain', cryptorain)
dispatcher.add_handler(cryptorain_handler)

tip_handler = CommandHandler('tip', tip)
dispatcher.add_handler(tip_handler)

balance_handler = CommandHandler('balance', balance)
dispatcher.add_handler(balance_handler)

commands_handler = CommandHandler('commands', help)
dispatcher.add_handler(commands_handler)

help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)

updater.start_polling()
