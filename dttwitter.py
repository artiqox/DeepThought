# dttwitter.py

import sys
import requests
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import tweepy
import subprocess
import sqlite3
import json
import re
from datetime import datetime, timedelta
from secrets import *
from hashids import Hashids

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

bot_username = 'GiveAIQ'
addvert = 'https://twitter.com/GiveAIQ/status/1126907758748622849'
core = "/home/debian/artiqox-node/artiqox-cli"
address = core
sqlite_file = '/home/debian/giveaiq/app.db'
earning_address = "ATUEvdfNGXT9B26HGhpE9B9JetxE9CDfBb"

class DictQuery(dict):
    def get(self, path, default = None):
        keys = path.split("/")
        val = None
        
        for key in keys:
            if val:
                if isinstance(val, list):
                    val = [ v.get(key, default) if v else None for v in val]
                else:
                    val = val.get(key, default)
            else:
                val = dict.get(self, key, default)
            
            if not val:
                break;

        return val

def get_voucher_number(id):
    hash_id = Hashids(salt=vouchers_salt, min_length=8)
    return hash_id.encode(id)

def get_voucher_id(voucher_number):
    hash_id = Hashids(salt=vouchers_salt, min_length=8)
    return hash_id.decode(voucher_number)[0]

def get_user_id(user_name, conn):
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    cmd = "select id from user where username = '{0}'".format(user_name)
    user_id = c.execute(cmd, ).fetchone()[0]
#    conn.close()
    return user_id

def get_status_id(status_name,conn):
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    cmd = "select id from giveaiq_status where name = '{0}'".format(status_name)
    status_id = c.execute(cmd, ).fetchone()[0]
#    conn.close()
    return status_id

def get_notify_me(user_name,conn):
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    cmd = "select notify_me from usertwitter where screen_name = '{0}'".format(user_name)
    print
    notify_me = c.execute(cmd, ).fetchone()[0]
#    conn.close()
    return notify_me

def get_promote_me(user_name,conn):
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    cmd = "select promote_me from usertwitter where screen_name = '{0}'".format(user_name)
    promote_me = c.execute(cmd, ).fetchone()[0]
#    conn.close()
    return promote_me

def change_user_tweet(user,conn):
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    cmd = "SELECT tweet FROM catchy_tweet ORDER BY RANDOM() LIMIT 1"
    catchy = c.execute(cmd, ).fetchone()[0]
    cmd = "UPDATE user SET confirm_my_stuff=? where username=?"
    c.execute(cmd, (catchy, user))
    conn.commit()
#    conn.close()

def get_balance(giveaiq_user_name):
    giveaiq_displayname = giveaiq_user_name[3:]
    giveaiq_accounttype = giveaiq_user_name[0:3]    
    result = subprocess.run([core,"getbalance",giveaiq_accounttype + giveaiq_displayname.lower()],stdout=subprocess.PIPE)
    clean = (result.stdout.strip()).decode("utf-8")
    return float(clean)

def update_usertwitter(user,conn):
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    cmd = "INSERT OR IGNORE INTO usertwitter (screen_name) VALUES (?)"
    c.execute(cmd, (user, ))
    conn.commit()
#    conn.close()

def update_tweet(tweet_id,conn):
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

def twitter_giver(giveaiq_user_name, giveaiq_user_name_target, amount_aiq, in_reply_to_status_id_str, conn):
    giveaiq_displayname = giveaiq_user_name[3:]
    giveaiq_accounttype = giveaiq_user_name[0:3]
    giveaiq_displayname_target = giveaiq_user_name_target[3:]
    giveaiq_accounttype_target = giveaiq_user_name_target[0:3] 
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    if in_reply_to_status_id_str:

        tx = subprocess.run([core,"move",giveaiq_accounttype + giveaiq_displayname.lower(),giveaiq_accounttype_target + giveaiq_displayname_target.lower(),amount_aiq, "1", str(in_reply_to_status_id_str)],stdout=subprocess.PIPE)
        cmd = "UPDATE twitter_tweet SET total_received_amount = total_received_amount + ?, total_received_number = total_received_number + 1 WHERE id=?"
        c.execute(cmd, (amount_aiq, in_reply_to_status_id_str, ))
        cmd = "UPDATE usertwitter SET total_received_amount = total_received_amount + ?, total_received_number = total_received_number + 1 WHERE screen_name=?"
        c.execute(cmd, (amount_aiq, giveaiq_displayname_target, ))
        cmd = "UPDATE usertwitter SET total_gives_amount = total_gives_amount + ?, total_gives_number = total_gives_number + 1 WHERE screen_name=?"
        c.execute(cmd, (amount_aiq, giveaiq_displayname, ))
        conn.commit()
    else:
        tx = subprocess.run([core,"move",giveaiq_accounttype + giveaiq_displayname.lower(),giveaiq_accounttype_target + giveaiq_displayname_target.lower(),amount_aiq],stdout=subprocess.PIPE)
        cmd = "UPDATE usertwitter SET total_received_amount = total_received_amount + ?, total_received_number = total_received_number + 1 WHERE screen_name=?"
        c.execute(cmd, (amount_aiq, giveaiq_displayname_target, ))
        cmd = "UPDATE usertwitter SET total_gives_amount = total_gives_amount + ?, total_gives_number = total_gives_number + 1 WHERE screen_name=?"
        c.execute(cmd, (amount_aiq, giveaiq_displayname, ))
        conn.commit()
#    conn.close()

def balance(user,tweetId,options):
    lowsymb = options.lower()
    uppsymb = options.upper()
    api_url = requests.get('https://api.coingecko.com/api/v3/coins/artiqox?localization=false')
    market_data_json = api_url.json()
    current_price_json = json.loads(json.dumps(market_data_json['market_data']))
    currency_json = json.loads(json.dumps(current_price_json['current_price']))
    if user is None:
        print("no user")
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
        
        result = subprocess.run([core,"getbalance","TW-" + user.lower()],stdout=subprocess.PIPE)
        clean = (result.stdout.strip()).decode("utf-8")
        balance  = float(clean)
        last_fiat = float(fiat_price)
        fiat_balance = balance * last_fiat
        fiat_balance = str(round(fiat_balance,decplace))
        balance =  str(round(balance,4))
        api.update_status('Hi @{0}, your current balance is: {1} AIQ ≈ {2}{3}. {4}'.format(user,balance,uppsymb,fiat_balance,addvert), tweetId)
    
def give(user,tweetId,amount,target,options,in_reply_to_status_id_str,conn):

    giveaiq_user_name = "TW-"+user
    giveaiq_user_name_target = "TW-"+target
    update_usertwitter(giveaiq_user_name[3:],conn)
    update_usertwitter(giveaiq_user_name_target[3:],conn)
    if get_notify_me(giveaiq_user_name_target[3:],conn) == 1:
        target_notify_me="@"+target
    else:
        target_notify_me=target

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
        #api.update_status('@{0} you have insufficent funds. {1}'.format(user,addvert), tweetId)
        print("User trying to give more than he has")
    elif target == user:
        #api.update_status('@{0} you can\'t give yourself AIQ. {1}'.format(user,addvert), tweetId)
        print("User trying to give himself")
    elif uppsymb == "AIQ":
        balance = str(balance)
        amount = str(amount)
        amount_aiq = str(round(amount_aiq,decplace))
        if in_reply_to_status_id_str:
            update_tweet(in_reply_to_status_id_str,conn)
            twitter_giver(giveaiq_user_name, giveaiq_user_name_target, amount_aiq, in_reply_to_status_id_str, conn)
        else:
            twitter_giver(giveaiq_user_name, giveaiq_user_name_target, amount_aiq, "", conn)
        amount_aiq = '{0:.8f}'.format(float(amount_aiq))
        api.update_status('Hi {1}, @{0} gave you {2} AIQ. {3}'.format(user, target_notify_me, amount_aiq, addvert), tweetId)
    else:
        balance = str(balance)
        amount = str(amount)
        amount_aiq = str(round(amount_aiq,decplace))
        if in_reply_to_status_id_str:
            update_tweet(in_reply_to_status_id_str,conn)
            twitter_giver(giveaiq_user_name, giveaiq_user_name_target, amount_aiq, in_reply_to_status_id_str, conn)
        else:
            twitter_giver(giveaiq_user_name, giveaiq_user_name_target, amount_aiq, "", conn)
        amount_aiq = '{0:.8f}'.format(float(amount_aiq))
        amount = '{0:.8f}'.format(float(amount))
        api.update_status('Hi {1}, @{0} gave you {2} AIQ ≈ {3}{4}. {5}'.format(user, target_notify_me, amount_aiq, uppsymb, amount, addvert), tweetId)

def deposit(user,tweetId,options):

    if options == "qr":
        result = subprocess.run([address,"getaccountaddress","TW-" + user.lower()],stdout=subprocess.PIPE)
        clean = (result.stdout.strip()).decode("utf-8")
        api.update_status('Hi @{0}, your depositing address is: {1} follow https://chart.googleapis.com/chart?cht=qr&chl=artiqox%3A{1}&chs=180x180&choe=UTF-8&chld=L|2 to get your QR code. {2}'.format(user, clean, addvert), tweetId)

    else:
        result = subprocess.run([address,"getaccountaddress","TW-" + user.lower()],stdout=subprocess.PIPE)
        clean = (result.stdout.strip()).decode("utf-8")
        api.update_status('Hi @{0}, your depositing address is: {1} {2}'.format(user, clean, addvert), tweetId)

def withdraw(user,tweetId,amount,target):

    address = ''.join(str(e) for e in target)
    
    amount = float(amount)
    
    result = subprocess.run([core,"getbalance","TW-" + user.lower()],stdout=subprocess.PIPE)
    clean = (result.stdout.strip()).decode("utf-8")
    balance = float(clean)
    if balance < amount:
        api.update_status('Hi @{0}, you have insufficent funds. {1}'.format(user,addvert), tweetId)
    else:
        amount = str(amount)
        tx = subprocess.run([core,"sendfrom","TW-" + user.lower(),address,amount],stdout=subprocess.PIPE)
        api.update_status('@{0} has successfully withdrew to address: {1} of {2} AIQ. {3}'.format(user,address,amount,addvert), tweetId)

def help(user,tweetId,options):

    if options == "give":

        api.update_status('Hi @{0}, give money replying to any tweet with "@{1} 1.5 USD" to give it\'s author $AIQ worth of 1.5 USD (use any ticker like EUR, GBP, BTC, ... if no matching currency amount will be in #AIQ). You can also tweet "@{1} @user 1.5" to give @user 1.5 AIQ.'.format(user,bot_username), tweetId)

    elif options == "deposit":
        
        api.update_status('Hi @{0}, Tweet "@{1} deposit" to see your deposit address for #AIQ, "@{1} deposit qr" shows the address and QR code.'.format(user,bot_username), tweetId)

    elif options == "balance":
        
        api.update_status('Hi @{0}, Tweet "@{1} balance" to see your current balance of #AIQ, "@{1} balance EUR" shows your balance in EUR.'.format(user,bot_username), tweetId)

    elif options == "withdraw":
        
        api.update_status('Hi @{0}, Tweet "@{1} withdraw xyz 20" to withdraw 20 #AIQ to wallet address xyz.'.format(user,bot_username), tweetId)

    else:

        api.update_status('Hi @{0}, give money by replying to any tweet with "@{1} 1.5 USD" to give it\'s author $AIQ worth of 1.5 USD. Check other #AIQ bot commands by tweeting "@{1} help give", "@{1} help balance", "@{1} help deposit" or "@{1} help withdraw"'.format(user,bot_username), tweetId)

def verification(user,tweettext,conn):
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    giveaiq_user_name = "TW-"+user
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
                cmd = "INSERT OR IGNORE INTO usertwitter (screen_name) VALUES (?)"
                c.execute(cmd, (user, ))
                conn.commit()
                change_user_tweet(giveaiq_user_name,conn)
                cmd = "DELETE FROM verification WHERE username=?"
                c.execute(cmd, (giveaiq_user_name, ))
                conn.commit()
                print("User {0} authorized".format(giveaiq_user_name))
#    conn.close()

def withdraw_orders(user,tweettext,conn):
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    giveaiq_user_name = "TW-"+user
    cmd = "SELECT id, target_wallet, amount FROM withdraw WHERE user_id=? and status=(select id from giveaiq_status where name=\"Withdraw Awaiting Confirmation\")"
    c.execute(cmd, (get_user_id(giveaiq_user_name, conn), ))
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
                cmd = "UPDATE withdraw SET status=(select id from giveaiq_status where name=\"Withdraw Cancelled\"), comment=\"Cancelled by twitter bot due to no funds\" WHERE id=?"
                c.execute(cmd, (id, ))
            else:
                amount = str(amount)
                tx = subprocess.run([core,"sendfrom","TW-" + user.lower(),address,amount],stdout=subprocess.PIPE)
                cmd = "UPDATE withdraw SET status=(select id from giveaiq_status where name=\"Withdraw Executed\"), comment=\"Executed by twitter bot\" WHERE id=?"
                c.execute(cmd, (id, ))
            conn.commit()
        cmd = "SELECT tweet FROM catchy_tweet where tweet not in (select confirm_my_stuff from user where username=?) ORDER BY RANDOM() LIMIT 1"
        c.execute(cmd, (giveaiq_user_name, ))
        catchy = c.fetchone()
        cmd = "UPDATE user SET confirm_my_stuff=? where username=?"
        c.execute(cmd, (catchy[0], giveaiq_user_name))
        conn.commit()
#    conn.close()

def voucher_orders(user,tweettext,conn):
    print("we are in the voucher_orders function")
    print(tweettext)
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    giveaiq_accounttype="TW-"
    giveaiq_user_name = "TW-"+user
    cmd = "SELECT id, amount FROM voucher WHERE user_id=? and status=(select id from giveaiq_status where name=\"Voucher Awaiting Confirmation\")"
    c.execute(cmd, (get_user_id(giveaiq_user_name,conn), ))
    vouchers_hash = c.fetchall()
    print("voucher hash:")
    print(vouchers_hash)
    cmd = "SELECT id, confirm_my_stuff FROM user WHERE username=?"
    c.execute(cmd , (giveaiq_user_name, ))
    id_confirm_my_stuff = c.fetchone()
    print(id_confirm_my_stuff)
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
    change_user_tweet(giveaiq_user_name,conn)
#    conn.close()

def promotedtweet_orders(user,tweettext,conn):
#    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    giveaiq_user_name = "TW-"+user
    print(get_status_id("Tweet Awaiting Confirmation",conn))
    cmd = "SELECT promoted_tweet.id, tweet_category.price, promoted_tweet.tweet_id FROM promoted_tweet, tweet_category WHERE promoted_tweet.cat_id=tweet_category.id and promoted_tweet.user_id=? and promoted_tweet.status=?"
    c.execute(cmd, (get_user_id(giveaiq_user_name,conn), get_status_id("Tweet Awaiting Confirmation",conn), ))
    promoted_tweets_hash = c.fetchall()
    print(promoted_tweets_hash)
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
            update_tweet(tweet_id,conn)
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
                    tx = subprocess.run([core,"sendfrom","TW-" + user.lower(),earning_address,amount],stdout=subprocess.PIPE)
                cmd = "UPDATE promoted_tweet set status=(select id from giveaiq_status where name=\"Promote Tweet Order Paid\"), activated_date=?, validtill_date=? WHERE id=?"
                c.execute(cmd, (current_time, one_day_ahead, id))
            conn.commit()
        cmd = "SELECT tweet FROM catchy_tweet where tweet not in (select confirm_my_stuff from user where username=?) ORDER BY RANDOM() LIMIT 1"
        c.execute(cmd , (giveaiq_user_name, ))
        catchy = c.fetchone()
        cmd = "UPDATE user SET confirm_my_stuff=? where username=?"
        c.execute(cmd, (catchy[0], giveaiq_user_name))
        conn.commit()
#    conn.close()

def cryptorain(user,tweetId,amount,options,receivers,conn):
    giveaiq_user_name = "TW-"+user
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

        if get_notify_me(receiver[1:],conn) == 1:
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
            tx = subprocess.run([core,"move","TW-" + user.lower(),"TW-" + target.lower(),amount_aiq],stdout=subprocess.PIPE)
            amount_aiq = '{0:.8f}'.format(float(amount_aiq))
            received_list = received_list+" "+target_notify_me
        else:
            balance = str(balance)
            amount = str(amount)
            amount_aiq = str(round(amount_aiq,decplace))
            tx = subprocess.run([core,"move","TW-" + user.lower(),"TW-" + target.lower(),amount_aiq],stdout=subprocess.PIPE)
            amount_aiq = '{0:.8f}'.format(float(amount_aiq))
            amount = '{0:.8f}'.format(float(amount))
            received_list = received_list+" "+target_notify_me
    if uppsymb == "AIQ" and len(received_list) >= 1:
        api.update_status('Hi @{0} #cryptorain {2} AIQ sent to your friends {5}'.format(user, received_list, amount_aiq, uppsymb, amount, addvert, str(len(received_list))), tweetId)
    elif len(received_list) >= 1:
        api.update_status('Hi @{0} #cryptorain {2} AIQ ≈ {3}{4} sent to your friends {5}'.format(user, received_list, amount_aiq, uppsymb, amount, addvert, str(len(received_list))), tweetId)

# create a class inheriting from the tweepy  StreamListener
class BotStreamer(tweepy.StreamListener):
    # Called when a new status arrives which is passed down from the on_data method of the StreamListener
    def on_data(self, data):
        conn = sqlite3.connect(sqlite_file)
        d = json.loads(data)
        if DictQuery(d).get("extended_tweet",None):
            tweet_text = d['extended_tweet']['full_text']
        else:
            tweet_text = d['text']
        user = d['user']['screen_name']
        tweetId = d['id']
        print(data)
        # give in case when user replies to somebody        
        pattern = r".*@" + re.escape(bot_username) + r" ([\d]+[\.]{0,1}[\d]*)\s*([a-zA-Z\d]{0,3}).*"
        match = re.match(pattern,tweet_text)
        if match and d['in_reply_to_screen_name'] != "None" and d['in_reply_to_screen_name'] != bot_username and user != bot_username and d['in_reply_to_screen_name']:
            give(user,tweetId,match.group(1),d['in_reply_to_screen_name'],match.group(2),d['in_reply_to_status_id_str'], conn)
        # give in case when user types giveaiq @targetUser amount
        pattern = r".*@" + re.escape(bot_username) + r" @([\w]+)\s*([\d]+[\.]{0,1}[\d]*)\s*([a-zA-Z\d]{0,3}).*"
        match = re.match(pattern,tweet_text)
        if match and user != bot_username and match.group(1) != bot_username:
            give(user,tweetId,match.group(2),match.group(1),match.group(3), d['in_reply_to_status_id_str'], conn)
        # withdraw of funds
#        pattern = r".*@" + re.escape(bot_username) + r" withdraw \b([a-z\dA-Z]{34})\b (\d+[\.]*[\d]*)\s*"
#        match = re.match(pattern,d['text'])
#        if match and user != bot_username:
#            #withdraw(user,tweetId,match.group(2),match.group(1))
#        # user checks balance
#        pattern = r".*@" + re.escape(bot_username) + r" (balance)\s*([\w]*).*"
#        match = re.match(pattern,d['text'])
#        if match and user != bot_username:
#            #balance(user,tweetId,match.group(2))
#        # user checks deposit
#        pattern = r".*@" + re.escape(bot_username) + r" (deposit)\s*([\w]*).*"
#        match = re.match(pattern,d['text'])
#        if match and user != bot_username:
#            #deposit(user,tweetId,match.group(2))
#        # user needs help
#        pattern = r".*@" + re.escape(bot_username) + r" (help)\s*([\w]*).*"
#        match = re.match(pattern,d['text'])
#        if match and user != bot_username:
#            #help(user,tweetId,match.group(2))
#        # grant access to giveAIQ
        pattern = r".*@GiveAIQ AIQ to the moon\.[\s]{1}([^#]+)\s#.*"
        match = re.match(pattern,tweet_text)
        if match and user != bot_username:
            verification(user,match.group(1),conn)

        pattern = r".*@GiveAIQ you guys rock![\s]{1}([^#]+)\s#.*"
        match = re.match(pattern,tweet_text)
        if match and user != bot_username:
            withdraw_orders(user,match.group(1),conn)

        pattern = r".*@GiveAIQ cryptorain ([\d]+[\.]{0,1}[\d]*)\s([0-9a-zA-Z]*)\s*(.*)"
        match = re.match(pattern,tweet_text)
        if match and user != bot_username:
            cryptorain(user,tweetId,match.group(1),match.group(2),match.group(3),conn)

        pattern = r".*@GiveAIQ AIQ supercrypto![\s]{1}([^#]+)\s#.*"
        match = re.match(pattern,tweet_text)
        if match and user != bot_username:
            promotedtweet_orders(user,match.group(1),conn)

        pattern = r".*@GiveAIQ AIQ cryptovouchers, so cool![\s]{1}([^#]+)\s#.*"
        match = re.match(pattern,tweet_text)
        if match and user != bot_username:
            voucher_orders(user,match.group(1),conn)
        conn.close()


myStreamListener = BotStreamer()
# Construct the Stream instance
stream = tweepy.Stream(auth, myStreamListener)
#stream.user_timeline(screen_name = bot_username, count = 1, include_rts = True)
track_me='@'+bot_username
stream.filter(track=[track_me])


