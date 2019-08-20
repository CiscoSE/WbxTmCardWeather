""" Copyright (c) 2019 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. """


from webexteamssdk import WebexTeamsAPI
import json
from os import environ
from requests import get


OPEN_WEATHER_KEY = environ['OPEN_WEATHER_KEY']

def get_current_weather(zipcode, units='imperial', key=OPEN_WEATHER_KEY, country='us'):
    '''
    function to handle the query to openweathermap.org
    '''
    api = 'http://api.openweathermap.org'
    current_weather = '/data/2.5/weather?zip={0},{1}&APPID={2}&units={3}'.format(zipcode, country, key, units)
    req_url = api+current_weather
    response = get(req_url)
    return response.json()


def get_attachments(self, id):
    '''
    Bound method added to the WebexTeamsAPI to get attachments for a new feature called Adaptive Cards
    '''
    json_data = self._session.get('/attachment/actions/' + id)
    return json_data

def lambda_handler(event, context):
    '''
    Lambda handler for web requests that come in to the function
    '''
    wbxapi = WebexTeamsAPI()
    # Bind a method to the WebexTeamsAPI class to handle getting attachments/cards
    WebexTeamsAPI.get_attachments = get_attachments

    input_card = {
                'contentType': 'application/vnd.microsoft.card.adaptive',
                'content': {
                    '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
                    'type': 'AdaptiveCard',
                    'version': '1.1',
                    'body': [
                        {
                            'type': 'TextBlock',
                            'text': 'Please enter your zip code for weather...',
                            'size': 'Large',
                            'color': 'Good'
                        },
                        {
                            'type': 'Input.Text',
                            'id': 'zip',
                            'placeholder': '23060',
                            'style': 'zip'
                        }
                    ],
                    'actions': [
                        {
                            'type': 'Action.Submit',
                            'title': 'Submit'
                        }
                    ]
                }
            }
    output_card = {
                'contentType': 'application/vnd.microsoft.card.adaptive',
                'content': {
                    '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
                    'type': 'AdaptiveCard',
                    'version': '1.1',
                    'body': [
                        {
                            'type': 'ColumnSet',
                            'columns': [
                                {
                                    'type': 'Column',
                                    'id': 'icon',
                                    'items': [
                                        {
                                            'type': 'Image',
                                            'url': 'http://openweathermap.org/img/wn/10d@2x.png',
                                            'id': 'weather_icon',
                                            'horizontalAlignment': 'Center'
                                        }
                                    ]
                                },
                                {
                                    'type': 'Column',
                                    'id': 'text',
                                    'items': [
                                        {
                                            "type": "TextBlock",
                                            "text": "Moseley",
                                            "id": "area",
                                            "color": "Good"
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": "Clear",
                                            "id": "weather",
                                            "color": "Good"
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": "87 F",
                                            "id": "temperature",
                                            "color": "Good"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
    }

    if event:
        webhook = json.loads(event['body'])

    if webhook['id'] == 'your_webhook_id' and webhook['resource'] == 'messages':
        room_id = webhook['data']['roomId']

        if room_id:
            wbxapi.messages.create(roomId=room_id, text='Oops! Something is broken or you are using the mobile app for which cards are not supported yet.', attachments=input_card)

    elif webhook['id'] == 'your_webhook_id' and webhook['resource'] == 'attachmentActions':
        submission_id = webhook['data']['id']

        if submission_id:
            submission_data = wbxapi.get_attachments(submission_id)
            zipcode = submission_data['inputs']['zip']
        
        if zipcode:
            weather = get_current_weather(zipcode)

        if weather:
            area_name = weather['name']
            weather_main = weather['weather'][0]['main']
            temperature = weather['main']['temp']
            # humidity = weather['main']['humidity']
            weather_icon = weather['weather'][0]['icon']

            # Update the card to output to the chat
            for col in output_card['content']['body'][0]['columns']:
                if col['id'] == 'icon':
                    col['items'][0]['url'] = 'http://openweathermap.org/img/wn/{0}@2x.png'.format(weather_icon)
                elif col['id'] == 'text':
                    for text in col['items']:
                        if text['id'] == 'area':
                            text['text'] = area_name
                        elif text['id'] == 'weather':
                            text['text'] = weather_main
                        elif text['id'] == 'temperature':
                            text['text'] = str(int(temperature)) + ' F'
            
            if webhook['data']['roomId']:
                print(output_card)
                wbxapi.messages.create(roomId=webhook['data']['roomId'], text='Oops! Something is broken or you are using the mobile app for which cards are not supported yet.', attachments=output_card)