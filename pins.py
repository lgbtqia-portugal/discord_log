#!/usr/bin/env python3

import enum
import json
import sys

import jinja2
import requests

import api_client

class MessageTypes(enum.IntEnum):
	# https://discord.com/developers/docs/resources/channel#message-object-message-types
	CHANNEL_PINNED_MESSAGE = 6

def main():
	if sys.argv[1] == 'fetch':
		guild_id = '109469702010478592'
		fetch(guild_id)
	elif sys.argv[1] == 'hydrate':
		hydrate()
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
			channel_data['name'] = channel['name']
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

def hydrate():
	with open('pins.json', 'r') as f:
		pins = json.load(f)
	try:
		with open('pins_hydrated.json', 'r') as f:
			channel_pins = json.load(f)
	except FileNotFoundError:
		channel_pins = {}

	try:
		client = api_client.APIClient()
		for channel_id, channel_data in pins.items():
			channel_messages = channel_pins.setdefault(channel_data['name'], [])
			hydrated_message_ids = {m['id'] for m in channel_messages}
			for pin in channel_data['pins']:
				assert pin['channel_id'] == channel_id
				if pin['message_id'] not in hydrated_message_ids:
					message = client.get_message(pin['channel_id'], pin['message_id'])
					channel_messages.append(message)
	except KeyboardInterrupt:
		print('caught ^C')
	finally:
		with open('pins_hydrated.json', 'w') as f:
			json.dump(channel_pins, f)

def render():
	with open('pins_hydrated.json', 'r') as f:
		channel_pins = json.load(f)
	with open('pins/index.jinja2', 'r') as f:
		template = jinja2.Template(f.read())
	with open('pins/index.html', 'w') as f:
		stream = template.stream({'channel_pins': channel_pins})
		stream.enable_buffering()
		stream.dump(f)

if __name__ == '__main__':
	main()
