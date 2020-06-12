#!/usr/bin/env python3

import collections
import json
import re
import sys

import requests

import api_client

def main():
	action = sys.argv[1]
	if action == 'fetch':
		guild_id = sys.argv[2]
		fetch(guild_id)
	elif action == 'render':
		render()
	else:
		sys.exit('expected fetch/render, got ' + action)

def fetch(guild_id):
	emoji_re = re.compile(r'<a?:(\w+):\d+>')

	client = api_client.APIClient()
	emojis = collections.defaultdict(lambda: collections.defaultdict(int))
	users = {}
	try:
		bookmark = None
		for message in iter_messages(client, guild_id):
			if message['type'] != 0: # 0 = DEFAULT
				continue
			month = message['timestamp'][:7]
			new_bookmark = (message['channel_id'], month)
			if new_bookmark != bookmark:
				bookmark = new_bookmark
				print(month)

			users[message['author']['id']] = message['author']['username']
			content_emojis = set()
			for emoji_match in emoji_re.finditer(message['content']):
				content_emojis.add(emoji_match.group(1))
			for name in content_emojis:
				emojis[name][message['author']['id']] += 1

			reactions = message.get('reactions', [])
			for reaction in reactions:
				name = reaction['emoji']['name']
				emoji_for_request = name
				if reaction['emoji']['id'] is not None:
					emoji_for_request = '%s:%s' % (name, reaction['emoji']['id'])
				reacted_users = client.get_reactions(message['channel_id'], message['id'], emoji_for_request)
				for user in reacted_users:
					users[user['id']] = user['username']
					emojis[name][user['id']] += 1
	except KeyboardInterrupt:
		pass

	with open('emoji_stats.json', 'w') as f:
		json.dump(emojis, f, indent='\t')
	with open('users.json', 'w') as f:
		json.dump(users, f, indent='\t')

def render():
	with open('users.json', 'r') as f:
		users = json.load(f)
	with open('emoji_stats.json', 'r') as f:
		emoji_stats = json.load(f)

	emojis = collections.Counter()
	user_overall_stats = collections.Counter()
	for emoji, user_emoji_stats in emoji_stats.items():
		count = 0
		for user, user_emoji_count in user_emoji_stats.items():
			count += user_emoji_count
			user_overall_stats[user] += user_emoji_count
		emojis[emoji] += count

	top_user_ids = [user_id for user_id, _ in user_overall_stats.most_common(20)]
	top_users = {user_id: users[user_id] for user_id in top_user_ids}

	top_emojis = {emoji: emoji_stats[emoji] for emoji, _ in emojis.most_common(100)}

	with open('emoji_user_stats.json', 'w') as f:
		json.dump({
			'users': top_users,
			'emojis': top_emojis,
		}, f, indent='\t')

def iter_messages(client, guild_id):
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
