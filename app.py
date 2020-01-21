# spyfall-for-line / app.py

import os
import json
from random import randint, shuffle
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

GAMES = {}
LOC_FILE = 'data.txt'
SECRET_LOC_FILE = 'secrets.txt'
MIN_PLAYERS = 2
MAX_PLAYERS = 8
DEVELOPER_NAME = 'b0nd'
NEW_LOC_LINE_LEN = 9

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

how_to_play = (
    "Welcome to Spyfall, a game where to have to figure out the spy among you. " + 
    "Every player starts with a location and a role in that location, " + 
    "except one person who doesn't know the location: the spy.\n" +
    "During the game, you will ask each other questions relating to your roles and location, " +
    "using questions specific enough to figure out who the spy is, " + 
    "but not specific enough that they figure out the location.\n"
    "At the end you will vote on who you think the spy is. " +
    "If you've guessed incorrectly, the spy wins. "
    "If you guessed correctly, the spy has a chance to guess the location, " +
    "and if they guess correctly, they win.\n" +
    "Type \'commands\' to see a list of the commands available."
)

command_list = (
    "Commands:\n" + 
    "1.\'join\': Adds you to the players list. The game supports 3-8 Players\n" +
    "2.\'locations\': Gives you a list of all the locations you can get\n" +
    "3.\'start\': Starts the game, sending each person their roles\n" +
    "4.\'players\': Gives player list with player numbers used to vote\n" +
    "5.\'quit\': ends the game early\n" +
    "6.\'vote PLAYER\': vote for player using their player number\n" +
    "7.\'vote end\': ends the voting\n" +
    "8.\'LOCATION\': For spy only, used to guess a location\n" +
    "9.\'rules\': how to play the game\n" +
    "10.\'commands\': gives list of commands\n"
)

@handler.add(JoinEvent)
def handle_join(event):
    new_game = {
        'game_start': False,
        'players': {},
        'num_players': 0,
        'location': None,
        'guess_correct': None,
        'developer_mode': False,
        'include_secrets': False
    }
    if isinstance(event.source, SourceGroup):
        game_ID = str(event.source.group_id)
    elif isinstance(event.source, SourceRoom):
        game_ID = str(event.source.room_id)
    GAMES[game_ID] = new_game
    str_output = "Welcome to Spyfall! type \'rules\' for how to play!"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=str_output))

@handler.add(LeaveEvent)
def handle_leave(event):
    if isinstance(event.source, SourceGroup):
        game_ID = str(event.source.group_id)
    elif isinstance(event.source, SourceRoom):
        game_ID = str(event.source.room_id)
    GAMES.pop(game_ID)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    output = None
    txt = str(event.message.text).lower()
    user_ID = str(event.source.user_id)
    if isinstance(event.source, SourceGroup):
        game_ID = str(event.source.group_id)
        user_name = str(line_bot_api.get_group_member_profile(game_ID,user_ID).display_name)
    elif isinstance(event.source, SourceRoom):
        game_ID = str(event.source.room_id)
        user_name = str(line_bot_api.get_room_member_profile(game_ID,user_ID).display_name)
    locations = return_locations(game_ID).split('\n')[1:-1]
    
    if txt == "locations":
        output = return_locations(game_ID)
    elif txt == "players":
        output = return_players(game_ID)
    elif txt == "rules":
        output = how_to_play
    elif txt == "commands":
        output = command_list
    elif txt == "join":
        if GAMES[game_ID]['num_players'] <= MAX_PLAYERS:
            if not (user_ID in GAMES[game_ID]['players']):
                GAMES[game_ID]['num_players'] += 1
                player_num = GAMES[game_ID]['num_players']
                GAMES[game_ID]['players'][user_ID] = {
                    'player_num': player_num, 
                    'player_name': user_name,
                    'role': None,
                    'votes': 0,
                    'voted': False
                }
                output = f'{user_name} has been added to the game as player {player_num}.'
            else:
                output = f'{user_name} is already in game.'
        else:
            output = "Maximum number of players has been reached."
    elif txt == "start":
        if GAMES[game_ID]['num_players'] < MIN_PLAYERS:
            output = "Not enough players."
        else:
            GAMES[game_ID]['game_start'] = True
            GAMES[game_ID]['location'] = random_location(game_ID)
            give_roles(game_ID)
    elif 'vote' in txt and user_ID in GAMES[game_ID]['players']:
        vote_txt = txt.split(" ")[1]
        if GAMES[game_ID]['players'][user_ID]['voted'] == False:
            if vote_txt in "12345678":
                for player in GAMES[game_ID]['players']:
                    if GAMES[game_ID]['players'][player]['player_num'] == vote_txt:
                        GAMES[game_ID]['players'][player]['votes'] += 1
                GAMES[game_ID]['players'][user_ID]['voted'] = True
                output = f'{user_name} voted for player {vote_txt}.'
            else:
                output = f'{user_name}, that is not a valid vote.'
        elif vote_text == end:
            max_ID = None
            max_votes = 0
            for player in GAMES[game_ID]['players']:
                if GAMES[game_ID]['players'][player]['votes'] > max_votes:
                    max_ID = player
                    max_votes = GAMES[game_ID]['players'][player]['votes']
            suspect = GAMES[game_ID]['players'][max_ID]['player_name']
            if GAMES[game_ID]['players'][max_ID]['role'] == 'Spy':
                GAMES[game_ID]['guess_correct'] = True
                output = f'You are correct! {suspect} was the spy! '
                output += "The spy now still has a chance to win if they type the name of the right location. "
                output += "Type \'locations\' to see a list of locations."
            else:
                output +=  f'Oh no! {suspect} was not the spy! '
                output += 'Better luck next time.'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=output))
                if isinstance(event.source, SourceGroup):
                    line_bot_api.leave_group(game_ID)
                elif isinstance(event.source, SourceRoom):
                    line_bot_api.leave_room(game_ID)
                return
    elif txt in locations:
        if GAMES[game_ID]['players'][user_ID]['role'] == 'Spy':
            if GAMES[game_ID]['guess_correct'] == True:
                if txt == GAMES[game_ID]['location']:
                    output = "Correct! The Spy wins!"
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=output))
                    if isinstance(event.source, SourceGroup):
                        line_bot_api.leave_group(game_ID)
                    elif isinstance(event.source, SourceRoom):
                        line_bot_api.leave_room(game_ID)
                    return
                else:
                    output = "Incorrect! The team wins!"
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=output))
                    if isinstance(event.source, SourceGroup):
                        line_bot_api.leave_group(game_ID)
                    elif isinstance(event.source, SourceRoom):
                        line_bot_api.leave_room(game_ID)
                    return
    elif txt == "quit":
        output = "Thanks for playing!"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=output))
        if isinstance(event.source, SourceGroup):
            line_bot_api.leave_group(game_ID)
        elif isinstance(event.source, SourceRoom):
            line_bot_api.leave_room(game_ID)
        return
    elif txt == "alohamora":
        output = return_secrets(game_ID)
    if txt == "developer " + DEVELOPER_NAME:
        GAMES[game_ID]['developer_mode'] = True
        output = "Developer Mode Activated."
    elif GAMES[game_ID]['developer_mode'] == True:
        if txt == 'print locations':
            with open(SECRET_LOC_FILE, 'r') as sec:
                sec_data = json.load(sec)
                print(sec_data)
            output = "Locations printed to terminal."
        elif txt == 'developer exit':
            GAMES[game_ID]['developer_mode'] = False
            output = "Developer Mode Deactivated."
        elif '\n' in txt:
            developer_txt = txt.split("\n")
            if developer_txt[0] == 'add new location':
                output = add_location(developer_txt)
            elif developer_txt[0] == 'delete location':
                output = delete_location(developer_txt)
    print(GAMES)
    if output != None:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=output))  

def random_location(game_ID):
    locations = []
    with open(LOC_FILE, 'r') as loc:
        loc_data = json.load(loc)
    with open(SECRET_LOC_FILE, 'r') as sec:
        sec_data = json.load(sec)
    for i in loc_data:
        locations.append(i)
    if GAMES[game_ID]['include_secrets'] == True:
        for i in sec_data:
            locations.append(i)
    return locations[randint(1,len(locations))]

def give_roles(game_ID):
    players = []
    with open(LOC_FILE, 'r') as loc:
        loc_data = json.load(loc)
    with open(SECRET_LOC_FILE, 'r') as sec:
        sec_data = json.load(sec)
    if GAMES[game_ID]['location'] in loc_data:
        roles = loc_data[GAMES[game_ID]['location']]
    elif GAMES[game_ID]['location'] in sec_data:
        roles = sec_data[GAMES[game_ID]['location']]
    for i in GAMES[game_ID]['players']:
        players.append(i)
    print(players)
    shuffle(players)
    GAMES[game_ID]['players'][players[0]]['role'] = 'Spy'
    players = players[1:]
    shuffle(roles)
    count = 0
    for player in players:
        GAMES[game_ID]['players'][player]['role'] = roles[count]
        count += 1

def return_locations(game_ID):
    output = 'Locations:\n'
    with open(LOC_FILE, 'r') as loc:
        loc_data = json.load(loc)
    with open(SECRET_LOC_FILE, 'r') as sec:
        sec_data = json.load(sec)
    for i in loc_data:
        output += f'{i}\n'
    if GAMES[game_ID]['include_secrets'] == True:
        for i in sec_data:
            output += f'{i}\n'
    return output

def return_secrets(game_ID):
    GAMES[game_ID]['include_secrets'] = True
    output = 'Wow, you\'ve unlocked the secret locations!\n'
    output += 'type \'locations\' to see all the new potential locations.'
    return output

def return_players(game_ID):
    count = 1
    output = "Players:\n"
    for player in GAMES[game_ID]['players']:
        player_name = GAMES[game_ID]['players'][player]['player_name']
        output += f'{count}. {player_name}\n'
        count += 1
    output += "Use player number to vote."
    return output

def add_location(developer_txt):
    with open(SECRET_LOC_FILE, 'r') as sec:
        sec_data = json.load(sec)
    if len(developer_txt) != NEW_LOC_LINE_LEN:
        output = "Location addition failed."
    else:
        new_roles = []
        for role in developer_txt[2:]:
            new_roles.append(role)
        sec_data[developer_txt[1]] = new_roles
        with open(SECRET_LOC_FILE, 'w') as json_file:
            json.dump(sec_data, json_file)
        output = "Location successfully added."
    return output

def delete_location(developer_txt):
    with open(LOC_FILE, 'r') as loc:
        loc_data = json.load(loc)
    with open(SECRET_LOC_FILE, 'r') as sec:
        sec_data = json.load(sec)
    if developer_txt[1] in loc_data:
        loc_data.pop(developer_txt[1])
        output = "Location successfully deleted"
    elif developer_txt[1] in sec_data:
        sec_data.pop(developer_txt[1])
        output = "Location successfully deleted"
    else:
        output = "Location deletion failed."
    with open(LOC_FILE, 'w') as json_file:
        json.dump(loc_data, json_file)
    with open(SECRET_LOC_FILE, 'w') as json_file:
        json.dump(sec_data, json_file)
    return output

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)