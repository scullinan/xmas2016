from chalice import Chalice
import boto3
import json
import datetime
import logging

app = Chalice(app_name='xmas2016')
app.log.setLevel(logging.DEBUG)

@app.route('/', api_key_required=False)
def index():
    return {
                'xmas_game': '2016',
                'rules': [
                    "No presents unless you are on the good list",
                    "Ask for a present too many times and you'll be on the naughty list",
                    "Email the present to stuart.cullinan@intelliflo.com and the first todo so gets lunch on me :)"
                ],
                'operations':[
                    {'Show me the game rules':'GET /'},
                    {"Where's my present?":'GET /present/[your name]'},
                    {"I've been really good":'POST /good_list/[your name]'},
                    {"No seriously, I've been really good":'DELETE /naughty_list/[your name]'},
                ]
            }

@app.route('/present/{name}', api_key_required=False)
def present(name):
    dynamodb = boto3.resource('dynamodb')
    good = dynamodb.Table('good_list')
    bad = dynamodb.Table('naughty_list')
    ask = dynamodb.Table('ask_count')
    present = dynamodb.Table('present')

    onbad = bad.get_item(Key={'name':name})
    app.log.debug(onbad)
    if 'Item' in onbad:
        return {'message':'No presents for those on the naughty list :('}

    ongood = good.get_item(Key={'name':name})

    if 'Item' in ongood:
        present.put_item(Item={'name':name,'date':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        return {'message': "Well done, here is your pressie",
        "present":"V2VsbCBkb25lLCB5b3VyIHByZXNlbnQgaXMgbHVuY2ggb24gbWUgaW4gSmFudWFyeSA6KS4gTWVycnkgWE1BUyBhbmQgSGFwcHkgbmV3IHllYXIh",
        "tip":"it's wrapped in base64 wrapping paper, you'll need to unwrap it"}

    app.log.debug("getting item from ask count")
    onask = ask.get_item(Key={'name':name})
    if 'Item' in onask:
        app.log.debug("putting item on naughty list")
        bad.put_item(Item={
                 'name': name,
                 'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
             })
        ask.delete_item(Key={'name':name})
        return {'message':"You've asked too many times, your on the naughty list now!"}
    else:
        ask.put_item(Item={'name':name})

    return {'message':'You need to be on the good list to get a present'}

@app.route('/good_list/{name}', methods=['POST'], api_key_required=False)
def good_list(name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('good_list')
    ask = dynamodb.Table('ask_count')

    ask.delete_item(Key={'name':name})

    item = table.get_item(Key={'name':name})

    if 'Item' in item:
        return {"message":"You are already on the good list"}

    table.put_item(Item={
                'name': name,
                'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return {'message': 'Well done, your on the good list :)'}

@app.route('/naughty_list/{name}', methods=['DELETE'], api_key_required=False)
def naught_list(name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('naughty_list')

    item = table.get_item(Key={'name':name})

    if 'Item' not in item:
        return {"message":"You weren't on the naughty list...hmm should you be?"}

    table.delete_item(Key={'name':name})

    return {'message': "You are off the naughty list! That doesn't necessarily mean you are on the good list though..."}
