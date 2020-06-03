#!/usr/bin/env python3

import collections
import re
import sys

import requests

import api_client

def main():
	guild_id = sys.argv[1]
	emoji_re = re.compile(r'<a?:(\w+):\d+>')

	emojis = collections.Counter()
	try:
		bookmark = None
		for message in iter_messages(guild_id):
			if message['type'] != 0: # 0 = DEFAULT
				continue
			month = message['timestamp'][:7]
			new_bookmark = (message['channel_id'], month)
			if new_bookmark != bookmark:
				bookmark = new_bookmark
				print(month)

			content_emojis = set()
			for emoji_match in emoji_re.finditer(message['content']):
				content_emojis.add(emoji_match.group(1))
			for name in content_emojis:
				emojis[name] += 1

			reactions = message.get('reactions', [])
			for reaction in reactions:
				name = reaction['emoji']['name']
				emojis[name] += reaction['count']
	except KeyboardInterrupt:
		pass

	for name, count in emojis.most_common():
		print(name, count)

def iter_messages(guild_id):
	client = api_client.APIClient()
	for channel in client.get_channels(guild_id):
		if channel['type'] != api_client.ChannelType.GUILD_TEXT:
			continue
		print('#' + channel['name'])
		try:
			yield from client.iter_messages(channel['id'], 662193114538311693) # 2020-01-01
		except requests.exceptions.HTTPError as e:
			if e.response.status_code != 403:
				raise

if __name__ == '__main__':
	main()
