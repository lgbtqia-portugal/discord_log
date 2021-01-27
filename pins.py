#!/usr/bin/env python3

import collections
import enum
import json
import re
import sys

import requests

import api_client

class MessageTypes(enum.IntEnum):
	# https://discord.com/developers/docs/resources/channel#message-object-message-types
	CHANNEL_PINNED_MESSAGE = 6

def main():
	if sys.argv[1] == 'fetch':
		guild_id = '109469702010478592'
		fetch(guild_id)
	elif sys.argv[1] == 'render':
		render()
	else:
		sys.exit('usage: %s fetch|render' % sys.argv[0])

def fetch(guild_id):
	try:
		with open('pins.json', 'r') as f:
			pins = json.load(f)
	except FileNotFoundError:
		pins = {}

	client = api_client.APIClient()
	try:
		for channel in client.get_channels(guild_id):
			if channel['type'] != api_client.ChannelType.GUILD_TEXT:
				continue
			print('#' + channel['name'])
			channel_data = pins.setdefault(channel['id'], {'last_message': 0, 'pins': []})
			try:
				for message in client.iter_messages(channel['id'], channel_data['last_message']):
					if message['type'] == MessageTypes.CHANNEL_PINNED_MESSAGE and \
							'message_reference' in message:
						channel_data['pins'].append(message['message_reference'])
					channel_data['last_message'] = message['id']
			except requests.exceptions.HTTPError as e:
				if e.response.status_code != 403:
					raise
	except KeyboardInterrupt:
		print('caught ^C')
	finally:
		with open('pins.json', 'w') as f:
			json.dump(pins, f)

def render():
	pass

if __name__ == '__main__':
	main()
