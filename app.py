# -*- coding: utf-8 -*-
from flask import Flask
import os
from requests_oauthlib import OAuth1Session
import urllib.parse
import json


app = Flask(__name__)

CONSUMER_KEY = os.environ['CONSUMER_KEY']
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
ACCESS_TOKEN_SECRET = os.environ['ACCESS_TOKEN_SECRET']


twitter = OAuth1Session(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET
)

@app.route('/')
def index():
    favorite_list_url = "https://api.twitter.com/1.1/favorites/list.json"
    favorite_list_url = add_query(favorite_list_url, {"count" : 5, "include_entities" : "true", "tweet_mode" : "extended"})
    res = twitter.get(favorite_list_url)

    if res.status_code != 200:
        print("GET FOVORITE_LIST REQUEST ERROR!!")
        raise Exception

    favorite_tweets = json.loads(res.text)

    media_tweet = favorite_tweets[0]
    return(media_tweet['full_text'])

def add_query(url, hash):
    query = urllib.parse.urlencode(hash, doseq=True)

    pr = urllib.parse.urlparse(url)
    pr = pr._replace(query=query)

    url = urllib.parse.urlunparse(pr)

    return url

if __name__ == '__main__':
    app.run()