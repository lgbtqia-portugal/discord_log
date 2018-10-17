from os import path

import config

def write(new_channels, new_users):
	channels = {}
	channels_path = path.join(config.log_dir, 'channels')
	try:
		with open(channels_path, 'rb') as f:
			for line in f:
				guild_id, channel_id, channel_name = line.rstrip(b'\n').split(b'|', 2)
				channels[channel_id.decode()] = (guild_id.decode(), channel_name.decode('utf-8'))
	except FileNotFoundError:
		pass
	channels.update(new_channels)
	with open(channels_path, 'wb') as f:
		for channel_id, (guild_id, name) in channels.items():
			_write_line(f, guild_id, channel_id, name)

	users = {}
	users_path = path.join(config.log_dir, 'users')
	try:
		with open(users_path, 'rb') as f:
			for line in f:
				user_id, username = line.rstrip(b'\n').split(b'|', 1)
				users[user_id.decode()] = username.decode('utf-8')
	except FileNotFoundError:
		pass
	users.update(new_users)
	with open(users_path, 'wb') as f:
		for user_id, username in users.items():
			_write_line(f, user_id, username)

def _write_line(f, *args):
	encoded = map(lambda arg: arg.encode('utf-8'), args)
	f.write(b'|'.join(encoded) + b'\n')

def sanitize_name(name):
	return name.replace('/', '_')
