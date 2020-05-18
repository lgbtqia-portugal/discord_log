#!/usr/bin/env python3

import dataclasses
import operator
import os
from os import path
import sys

import lz4framed

import api_client

def main():
	guild_path = sys.argv[1]

	guild_name = path.basename(guild_path)
	with open(path.normpath(path.join(guild_path, '..', 'guilds')), 'r') as f:
		for line in f:
			guild_id, name = line.rstrip('\n').split('|', 1)
			if name == guild_name:
				break
		else:
			raise Exception("couldn't find guild ID for %s" % guild_name)

	users = {}
	for member in iter_members(guild_id):
		user = User(id=member['user']['id'], name=member['user']['username'],
				nick=member['nick'], joined=member['joined_at'], last_message='')
		users[user.id] = user

	for channel in os.listdir(guild_path):
		channel_path = path.join(guild_path, channel)
		for filename in os.listdir(channel_path):
			full_path = path.join(channel_path, filename)
			process_file(users, full_path)

	for user in sorted(users.values(), key=operator.attrgetter('last_message')):
		print('%-25s %-25s %s\t%s' % (user.name, user.nick or '', user.joined, user.last_message))

def iter_members(guild_id):
	client = api_client.APIClient()
	after = None
	while True:
		members = client.get_members(guild_id, after)
		yield from members
		if len(members) < 1000:
			break
		after = members[-1]['user']['id']

@dataclasses.dataclass
class User:
	id: str
	name: str
	nick: str
	joined: str
	last_message: str

def process_file(users, full_path):
	date = path.splitext(path.basename(full_path))[0]
	with open(full_path, 'rb') as f:
		compressed = f.read()
	contents = lz4framed.decompress(compressed)
	if contents[-1] != 0:
		raise Exception('corrupt log file', full_path)
	for message in contents.split(b'\0')[:-1]:
		msg_id, time, author_id, contents = message.split(b'|', 3)
		author_id = author_id.decode('utf-8')
		user = users.get(author_id)
		if user is not None:
			user.last_message = date

if __name__ == '__main__':
	main()
