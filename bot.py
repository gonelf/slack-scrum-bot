import os
import time
# from datetime import datetime, timedelta
from pytz import timezone
import pytz
import datetime
import time
import json
from slackclient import SlackClient

START = False
NEWDAY = True

# starterbot's ID as an environment variable
BOT_ID = 'U866S4HQC'
SLACK_BOT_TOKEN='xoxb-278230153828-FNjnHIVJ2uWOD0Dy8SjIKv8B'

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = 'do'
SCRUM_COMMAND = 'scrum'
MAIN_CHANNEL = '#test'

users = ['gonelf']
questions = ['What did you accomplished yesterday?',
             'What will you work on today?',
             'Do you have any blocker?',
             'Thank you for your time, See you tomorrow']

scrum_count = {}

# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_BOT_TOKEN)

def checktime():
    global START, NEWDAY
    eastern = timezone('US/Eastern')
    eastern.zone

    lisbon = timezone('Europe/Lisbon')

    now = datetime.datetime.now(tz=lisbon).time()
    tag = datetime.time(hour=10)
    day = datetime.time(hour=00, minute=00)

    if now > tag and NEWDAY:
        START = True
    if now.hour == day.hour and now.minute == day.minute:
        START = False
        NEWDAY = True

def send_message(message, target):
    slack_client.api_call("chat.postMessage", channel=target,
                          text=message, as_user=True)

def handle_command(command, channel, message):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    if command.startswith(SCRUM_COMMAND):
        if channel not in scrum_count.keys():
            scrum_count[channel] = {'count':0, 'messages':[]}

        if scrum_count[channel]['count'] < 4:
            scrum_count[channel]['messages'].append(message)
            response = questions[scrum_count[channel]['count']]
            scrum_count[channel]['count']+=1
        else:
            response = "A Scrum a day keeps the manager away"

    send_message(response, channel)

    if scrum_count[channel]['count'] == 4:
        send_message(scrum_count[channel]['messages'], MAIN_CHANNEL)
        scrum_count[channel]['count'] += 1

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        # print (output_list)
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel'], output['text']
            if output['type'] == 'message' and not output['user'] == BOT_ID:
                return 'scrum', output['channel'], output['text']

    return None, None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 0.5 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        checktime()
        if START:
            for user in users:
                send_message("hello", '@{}'.format(user))
            NEWDAY = False
        while True:
            checktime()
            command, channel, message = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel, message)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")