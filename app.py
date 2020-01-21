# spyfall-for-line / app.py

import os
import json
from decouple import config
from flask import (
    Flask, request, abort
)
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    FollowEvent, JoinEvent, LeaveEvent
)

app = Flask(__name__)
games = {}
LOC_FILE = 'data.txt'

# get LINE_CHANNEL_ACCESS_TOKEN from your environment variable
line_bot_api = LineBotApi(
    config("LINE_CHANNEL_ACCESS_TOKEN",
           default=os.environ.get('LINE_ACCESS_TOKEN'))
)
# get LINE_CHANNEL_SECRET from your environment variable
handler = WebhookHandler(
    config("LINE_CHANNEL_SECRET",
           default=os.environ.get('LINE_CHANNEL_SECRET'))
)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(JoinEvent)
def handle_join(event):
    if isinstance(event.source, SourceGroup):
        game_ID = event.SourceGroup.group_id
    if isinstance(event.source, SourceRoom):
        game_ID = event.SourceRoom.user_id
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=str(game_ID)))

@handler.add(LeaveEvent)
def handle_leave(event):
    pass

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == 'location all':
        loc_message = return_locations()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=loc_message))
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text))

def return_locations():
    output = 'Locations:\n'
    with open(LOC_FILE, 'r') as loc:
        loc_data = json.load(loc)
    for i in loc_data:
        output += f'{i}\n'
    return output

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)