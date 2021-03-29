#! /usr/bin/env python3

import flask
import requests
import json
import os.path
import googletrans
import markdown_strings as markdown

msgFile = '/tmp/messages.log'

telegramBotUrl = 'https://api.telegram.org/bot{botId}/sendMessage'
telegramBotId = '1680826928:AAHSJt-AWAMvUKvhyLLkq4KG8E-5Pd-DKAo'
alliaceWarChannelId  = '-1001290191382'
alliaceChatChannelId = '-1001326873478'
otherChannelId       = '-1001432977274'
translationString = ("*{player}*"
                     "\n{orig}"
                     "\n\n_Translation:_"
                     "\n{trans}"
                     "\nTranslated from _{src}_ to _{dest}_"
                    )


if os.path.exists(msgFile):
    with open(msgFile) as f:
        messageLog = f.readlines()
else:
    messageLog = []

app = flask.Flask(__name__)

def escape(text):
    badChars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '='
               ,'|', '{', '}', '.', '!'
               ]
    escapedText = str(text)
    for c in badChars:
        escapedText = escapedText.replace(c, '\\' + c)
    return escapedText

def translate(text):
    translator = googletrans.Translator()
    return translator.translate(text)

def sendTelegramMessage(chatId, botId, message):
    print("Sending message:", message)
    payload = {'chat_id': chatId, 'text': message, 'parse_mode': 'MarkdownV2'}
    r = requests.post(telegramBotUrl.format(botId=botId), json=payload, timeout=5)
    print("Response:", r.content)

def isolateNewMessages(messages):
    global messageLog
    nMessages = len(messages)

    oldMessages = []
    rxMessages = []
    newMessages = messages
    isMatch = True
    for offset in range(-nMessages, 0): 
        if -offset > len(messageLog):
            continue
        rxMessages = messages[0:-offset]
        oldMessages = messageLog[offset:]
        isMatch = True
        for log, rx in zip(oldMessages, rxMessages):
            if not log.startswith(rx):
                isMatch = False
                break
        if isMatch:
            newMessages = messages[-offset:]
            print("offset found:", offset)
            break


    print()
    print("Overlapping Messages:")
    for log, rx in zip(oldMessages, rxMessages):
        print(log)
        print(rx)
        print()
    print("New Messages:")
    for m in newMessages:
        print(m)

    return newMessages

@app.route('/evony', methods=['POST'])
def handleEvonyPost():
    global messageLog
    print('handleEvonyPost(): Begin...')
    with open('/tmp/evony.log', 'a') as f:
        f.write("\n")
        f.write(flask.request.mimetype)
        f.write(str(flask.request.data))
    data = flask.request.data.decode('utf-8')
    messages = data.splitlines()
    messages.reverse()
    with open('/tmp/evony.log', 'a') as f:
        f.write("Recieved Messages:")
        for m in messages:
            f.write(m)
            print(m)

    newMessages = isolateNewMessages(messages)
    messageLog += newMessages
    with open(msgFile, 'a') as f:
        for m in newMessages:
            f.write(m + '\n')

    for m in newMessages:
        if m.startswith('My Liege, the horns of war are sounding'):
            message = escape(m)
            sendTelegramMessage(alliaceWarChannelId, telegramBotId, message)
        elif m.startswith('[369]'):
            mSplit = m[5:].split(':')
            mPlayer = mSplit[0]
            mText = ':'.join(mSplit[1:])
            translated = translate(mText)
            if translated.src == translated.dest:
                message = ("*" + escape(mPlayer) + "*"
                          + "\n"
                          + escape(mText)
                          )
                sendTelegramMessage(alliaceChatChannelId, telegramBotId, message)
            else:
                message = translationString.format(
                                  player=escape(mPlayer)
                                 ,orig=escape(mText)
                                 ,trans=escape(translated.text)
                                 ,src=escape(translated.src)
                                 ,dest=escape(translated.dest)
                                                  )
                sendTelegramMessage(alliaceChatChannelId
                                   ,telegramBotId
                                   ,message
                                   )
                                                           
        else:
            message = escape(m)
            sendTelegramMessage(otherChannelId, telegramBotId, message)

    return "Received"

app.run(host='0.0.0.0', port=8217)
