from os import path

import lz4framed

import config

channel_logs = {}

def log_message(message):
	channel_path = path.join(message.server.name, message.channel.name)
	date = message.timestamp.date()
	cl = channel_logs.get(channel_path)
	if cl is not None and cl.date != date:
		cl.close()
		cl = None
	if cl is None:
		cl = ChannelLog(channel_path, date)
		channel_logs[channel_path] = cl
	cl.log(message.id, message.timestamp.strftime('%H:%M:%S'),
			message.author.display_name, message.clean_content)

def last_message_id(abspath):
	with open(abspath, 'rb') as f:
		contents = lz4framed.decompress(f.read())
		if contents[-1] != 0:
			raise Exception('corrupt log file', abspath)
		last_message = contents[contents.rfind(b'\0', 0, -1) + 1:-1]
		return last_message.split(b'|', 1)[0].decode()

class ChannelLog:
	def __init__(self, channel_path, date):
		abspath = path.join(config.log_dir, channel_path, date.strftime('%Y-%m-%d'))
		try:
			self.file = open(abspath, 'xb')
		except FileExistsError:
			with open(abspath, 'rb') as f:
				contents = lz4framed.decompress(f.read())
			self.file = open(abspath, 'wb')
		else:
			contents = None
		self.compressor = lz4framed.Compressor(self.file)
		if contents:
			self.compressor.update(contents)

		self.date = date

	def log(self, *args):
		line = '|'.join(args).encode('utf-8')
		self.compressor.update(line + b'\0')

	def close(self):
		self.compressor.end()
		self.file.close()
