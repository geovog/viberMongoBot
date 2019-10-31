import pymongo
import requests
from datetime import datetime
from pymongo import MongoClient
from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import VideoMessage
from viberbot.api.messages import RichMediaMessage
from viberbot.api.messages.text_message import TextMessage

import logging

from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest

app = Flask(__name__)
viber = Api(BotConfiguration(
	name='YourBotName',
	avatar='https://img.icons8.com/ultraviolet/40/000000/avatar.png',
	auth_token='YourAuthToken'
))

logger = logging.getLogger()
logging.basicConfig(filename='viberBot.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
client = MongoClient('mongodb://localhost:27017')
db = client['netlinkBot']


@app.route('/', methods=['POST'])
def incoming():
    logger.debug("received request. post data: {0}".format(request.get_data()))
    # every viber message is signed, you can verify the signature using this method
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberConversationStartedRequest):
        userDtl = db.subusers
        eventDtl = db.eventData
        if userDtl.find({'userId': viber_request.user.id}).count() == 0:
            post_data = {
                'userId': viber_request.user.id,
                'userName': viber_request.user.name,
                'subscribed': False
            }
            result = userDtl.insert_one(post_data)
            logger.debug("One post: {0}".format(result.inserted_id))
        event_data= {
                'userId': viber_request.user.id,
                'event': 'ViberConversationStarted',
                'timestamp': datetime.now()
            }
        result = eventDtl.insert_one(event_data)
        logger.debug("One post: {0}".format(result.inserted_id))
        viber.send_messages(viber_request.user.id, [
            TextMessage(text="Welcome "+str(" " if viber_request.user.name is None else viber_request.user.name)+"!")
        ])
        url = "https://chatapi.viber.com/pa/send_message"
        payload = "{\r\n   \"receiver\":\""+viber_request.user.id+"\",\r\n   \"type\":\"rich_media\",\r\n   \"min_api_version\":2,\r\n   \"rich_media\":{\r\n      \"Type\":\"rich_media\",\r\n      \"ButtonsGroupColumns\":6,\r\n      \"ButtonsGroupRows\":7,\r\n      \"BgColor\":\"#FFFFFF\",\r\n      \"Buttons\":[\r\n         {\r\n            \"Columns\":6,\r\n            \"Rows\":3,\r\n            \"ActionType\":\"open-url\",\r\n            \"ActionBody\":\"https://www.netlink.gr\",\r\n            \"Image\":\"https://www.netlink.gr/wp-content/uploads/2017/09/netlink-logo.png\"\r\n         },\r\n         {\r\n            \"Columns\":6,\r\n            \"Rows\":2,\r\n            \"Text\":\"<font color=#323232><b>Επικοινωνήστε μαζί μας</b></font>\",\r\n            \"ActionType\":\"open-url\",\r\n            \"ActionBody\":\"https://www.netlink.gr/contact/\",\r\n            \"TextSize\":\"medium\",\r\n            \"TextVAlign\":\"middle\",\r\n            \"TextHAlign\":\"left\"\r\n         },\r\n         {\r\n            \"Columns\":6,\r\n            \"Rows\":1,\r\n            \"ActionType\":\"reply\",\r\n            \"ActionBody\":\"https://www.netlink.gr/contact/\",\r\n            \"Text\":\"<font color=#ffffff>Contact</font>\",\r\n            \"TextSize\":\"large\",\r\n            \"TextVAlign\":\"middle\",\r\n            \"TextHAlign\":\"middle\",\r\n            \"Image\":\"https://img.pngio.com/png-blue-toggle-button-png-toggle-button-button-material-vector-toggle-button-png-button-png-260_260.png\"\r\n         },\r\n         {\r\n            \"Columns\":6,\r\n            \"Rows\":1,\r\n            \"ActionType\":\"reply\",\r\n            \"ActionBody\":\"https://www.netlink.gr/about-us/\",\r\n            \"Text\":\"<font color=#8367db>MORE DETAILS</font>\",\r\n            \"TextSize\":\"small\",\r\n            \"TextVAlign\":\"middle\",\r\n            \"TextHAlign\":\"middle\"\r\n         }\r\n      ]\r\n   }\r\n}"
        headers = {
            'X-Viber-Auth-Token': "YourAuthToken",
            'Content-Type': "application/json",
            'User-Agent': "PostmanRuntime/7.19.0",
            'Accept': "*/*",
            'Cache-Control': "no-cache",
            'Host': "chatapi.viber.com",
            'Accept-Encoding': "gzip, deflate",
            'Content-Length': "1717",
            'Connection': "keep-alive",
            'cache-control': "no-cache"
        }
        response = requests.request("POST", url, data=payload.encode('utf-8'), headers=headers)
        logger.debug("received respones: {0}".format(response.text))
    elif isinstance(viber_request, ViberMessageRequest):
        message = viber_request.message
        # lets echo back
        if viber_request.message.text == "https://www.netlink.gr/contact/" or viber_request.message.text == "https://www.netlink.gr/about-us/":
            viber.send_messages(viber_request.sender.id, [
                message
            ])
    elif isinstance(viber_request, ViberSubscribedRequest):
        userDtl = db.subusers
        eventDtl = db.eventData
        if userDtl.find({'userId': viber_request.user.id}).count() == 0:
            post_data = {
                'userId': viber_request.user.id,
                'userName': viber_request.user.name,
                'subscribed': True
            }
            result = userDtl.insert_one(post_data)
            logger.debug("One post: {0}".format(result.inserted_id))
        else:
            userDtl.update_one(
                {"userId": viber_request.user.id},
                {
                    "$set": {
                        'subscribed': True
                    }
                }
            )
        event_data= {
                'userId': viber_request.user.id,
                'event': 'ViberSubscribed',
                'timestamp':  datetime.now()
            }
        result = eventDtl.insert_one(event_data)
        logger.debug("One post: {0}".format(result.inserted_id))
        viber.send_messages(viber_request.user.id, [
            TextMessage(text="thanks for subscribing!")
        ])
    elif isinstance(viber_request, ViberUnsubscribedRequest):
        userDtl = db.subusers
        eventDtl = db.eventData
        if userDtl.find({'userId': viber_request.user_id}).count() == 0:
            post_data = {
                'userId': viber_request.user_id,
                'userName': '',
                'subscribed': False
            }
            result = userDtl.insert_one(post_data)
            logger.debug("One post: {0}".format(result.inserted_id))
        else:
            userDtl.update_one(
                {"userId": viber_request.user_id},
                {
                    "$set": {
                        'subscribed': False
                    }
                }
            )
        event_data= {
                'userId': viber_request.user_id,
                'event': 'ViberUnsubscribed',
                'timestamp': datetime.now()
            }
        result = eventDtl.insert_one(event_data)
        logger.debug("One post: {0}".format(result.inserted_id))
    elif isinstance(viber_request, ViberFailedRequest):
        logger.warn("client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)

@app.route('/messageAll', methods=['POST'])
def postMessages():
    logger.debug("received request. post data: {0}".format(request.get_data()))
    req_data = request.get_json()
    message = req_data['text']
    userDtl = db.subusers
    subscribedUsrs = userDtl.find({'subscribed': True})
    for subuser in subscribedUsrs:
        viber.send_messages(subuser['userId'], [
            TextMessage(text=message)
        ])
    
    return Response(status=200)

if __name__ == "__main__":
    
    app.run(host='0.0.0.0', debug=False)
