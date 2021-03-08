# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, json
import os
from requests_oauthlib import OAuth1Session
import urllib.parse
import json

from flask_cors import CORS, cross_origin # ADD

from models.models import Families, Affiliation, Stocks
from models.database import db_session


from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

from array import array
import os
from PIL import Image
import sys
import time


app = Flask(__name__)
# CORS(app)
# CORS(app, support_credentials=True) # ADD
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['CORS_HEADERS'] = 'Content-Type'

app.config['JSON_AS_ASCII'] = False

CONSUMER_KEY = os.environ['CONSUMER_KEY']
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
ACCESS_TOKEN_SECRET = os.environ['ACCESS_TOKEN_SECRET']

SUBSCRIPTION_KEY = os.environ['AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY']
ENDPOINT = os.environ['AZURE_COMPUTER_VISION_ENDPOINT']


twitter = OAuth1Session(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET
)


@app.route('/get-favorites/<string:family_id>')
def get_favorites(family_id):
    with open('responses/get_favorites.json',  mode="r", buffering=-1, encoding='utf-8') as f:
        res = json.loads(f.read())
    
    twi_ids = []
    all_family_member = db_session.query(Affiliation).filter(Affiliation.family_id == family_id).all()

    for m in all_family_member:
        twi_ids.append(m.twi_id)

    for twi_id in twi_ids:
        favorite_tweets = get_favorite_tweets(twi_id)
        hash = collect_favorite_img_tweet(favorite_tweets)
        res["res"].extend(hash)

    
    return jsonify(res)


def get_favorite_tweets(twi_id):
    favorite_list_url = "https://api.twitter.com/1.1/favorites/list.json"
    favorite_list_url = add_query(favorite_list_url, {"screen_name" : twi_id, "count" : 5, "include_entities" : "true", "tweet_mode" : "extended"})
    res = twitter.get(favorite_list_url)

    if res.status_code != 200:
        print("GET FOVORITE_LIST REQUEST ERROR!!")
        raise Exception

    favorite_tweets = json.loads(res.text)

    return(favorite_tweets)

def collect_favorite_img_tweet(favorite_tweets):
    res = []
    for favorite_tweet in favorite_tweets:
        if 'media' in favorite_tweet["entities"]:
            img_url = favorite_tweet["entities"]['media'][0]["media_url_https"]

            id = favorite_tweet["id"]
            sc_name = favorite_tweet["user"]["screen_name"]
            tw_url = "https://twitter.com/{}/status/{}".format(sc_name, id)

            res.append({"img":img_url, "link":tw_url})
    
    return res


@app.route('/debug')
def debug():
    res = {"family":[], "affiliation":[], "stocks":[]}

    for f in Families.query.all():
        res["family"].append(f.family_id)

    for f in Affiliation.query.all():
        res["affiliation"].append(f.twi_id)

    for f in Stocks.query.all():
        res["stocks"].append(f.twi_link)


    return jsonify(res)


@app.route('/vision-debug')
def v_debeg():
    computervision_client = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(SUBSCRIPTION_KEY))
    twi_img = "https://radichubu.jp/files/topics/17395_ext_01_0.jpeg"
    tags_result_remote = computervision_client.tag_image(twi_img )

    res = {"res" : []}
    for tag in tags_result_remote.tags:
        res["res"].append("'{}' with confidence {:.2f}%".format(tag.name, tag.confidence * 100))

    return jsonify(res)




@app.route('/create-family', methods=['POST'])
def create():    
    # family_id = request.form['family_id']
    # twi_id = request.form['twi_id']

    f = request.get_data()
    form_data = json.loads(f.decode('utf-8'))
    family_id = form_data['family_id']
    twi_id = form_data['twi_id']

    # save Families table
    f_object = Families(family_id=family_id)
    db_session.add(f_object)
    db_session.commit()

    # save Affiliation table
    a_object = Affiliation(family_id=family_id, twi_id=twi_id)
    db_session.add(a_object)
    db_session.commit()

    return get_favorites(family_id)


@app.route('/enter/<string:family_id>')
def enter(family_id):
    return get_favorites(family_id)


@app.route('/create-stock', methods=['POST'])
def stock():
    # family_id = request.form['family_id']
    # twi_link = request.form['twi_link']

    f = request.get_data()
    form_data = json.loads(f.decode('utf-8'))
    family_id = form_data['family_id']
    twi_link = form_data['twi_link']

    s = db_session.query(Stocks).filter(Stocks.family_id == family_id).first()
    if not s:
        s_object = Stocks(family_id=family_id, twi_link=twi_link)
        db_session.add(s_object)
        db_session.commit()
    else:
        s.twi_link = twi_link
        db_session.commit()


    return show_stock(family_id)


@app.route('/delete-stock', methods=['POST'])
def delete_stock():
    # return jsonify(dict(request.headers))

    
    # family_id = request.form.get('family_id')

    f = request.get_data()
    form_data = json.loads(f.decode('utf-8'))
    family_id = form_data['family_id']


    if family_id == None:
        return jsonify(dict(request.headers))

    s = db_session.query(Stocks).filter(Stocks.family_id == family_id).first()
    db_session.delete(s)
    db_session.commit()

    return show_stock(family_id)


@app.route('/show-stock/<string:family_id>')
def show_stock(family_id):
    res = {"twi_link" : ""}
    s = db_session.query(Stocks).filter(Stocks.family_id == family_id).first()

    if s:
        res["twi_link"] = s.twi_link
    else:
        res["twi_link"] = "nothing"

    return res


@app.route('/show-config/<string:family_id>')
def show(family_id):
    with open('responses/config.json',  mode="r", buffering=-1, encoding='utf-8') as f:
        res = json.loads(f.read())

    all_family_member = db_session.query(Affiliation).filter(Affiliation.family_id == family_id).all()

    for m in all_family_member:
        res['twi_id'].append(m.twi_id)
    
    return jsonify(res)


@app.route('/update-config', methods=['POST'])
def update():
    # family_id = request.form['family_id']
    # twi_id = request.form['twi_id']

    f = request.get_data()
    form_data = json.loads(f.decode('utf-8'))
    family_id = form_data['family_id']
    twi_id = form_data['twi_id']

    a_object = Affiliation(family_id=family_id, twi_id=twi_id)
    db_session.add(a_object)
    db_session.commit()

    return show(family_id)





def add_query(url, hash):
    query = urllib.parse.urlencode(hash, doseq=True)

    pr = urllib.parse.urlparse(url)
    pr = pr._replace(query=query)

    url = urllib.parse.urlunparse(pr)

    return url

if __name__ == '__main__':
    app.run()