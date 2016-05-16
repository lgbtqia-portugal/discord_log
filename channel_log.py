from collections import defaultdict
import datetime
import os
from os import path

import lz4framed

import config

channel_logs = {}
log_buffer = defaultdict(list) # when fetching history, log new messages to here
buffering_new = True

def log_message(message, old=False):
	channel_path = path.join(message.server.name, message.channel.name)
	if not old and buffering_new:
		log_buffer[channel_path].append(message)
		return

	date = message.timestamp.date()
	cl = channel_logs.get(channel_path)
	if cl is not None and cl.date != date:
		if cl.date > date:
			raise Exception('new message is older than previously logged')
		cl.close()
		cl = None
	if cl is None:
		cl = ChannelLog(channel_path, date)
		channel_logs[channel_path] = cl
	cl.log(message.id, message.timestamp.strftime('%H:%M:%S'),
			message.author.display_name, message.clean_content, old=old)

def flush_buffered():
	global buffering_new, log_buffer
	buffering_new = False

	count = 0
	for buf in log_buffer.values():
		for message in buf:
			log_message(message) # get_history may have already logged, but ChannelLog.log checks lmi
			count += 1
	del log_buffer
	print('flushed', count, 'buffered messages')

def last_message_id(abspath):
	return _parse(abspath)[0]

def _parse(abspath):
	with open(abspath, 'rb') as f:
		contents = f.read()
	if abspath.endswith('.lz4'):
		contents = lz4framed.decompress(contents)
		if contents[-1] != 0:
			raise Exception('corrupt log file', abspath)
	last_message = contents[contents.rfind(b'\0', 0, -1) + 1:-1]
	lmi = last_message.split(b'|', 1)[0].decode()
	return lmi, contents

def search(server, channel, query):
	channel_dir = path.join(config.log_dir, server, channel)
	query = query.casefold().split()
	results = []
	for filename in sorted(os.listdir(channel_dir), reverse=True):
		abspath = path.join(channel_dir, filename)
		contents = _parse(abspath)[1]
		lines = contents.split(b'\0')
		for line in lines[:-1]:
			_, time, user, text = line.split(b'|', 3)
			text = text.decode('utf-8')
			split = text.casefold().split()
			if split[0] == '!search' or user == b'log':
				continue
			for term in query:
				if term not in split:
					break
			else: # found all terms
				date_str = filename
				if filename.endswith('.lz4'):
					date_str = date_str[:10]
				time_str = '%s %s' % (date_str, time.decode('utf-8'))
				dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
				results.append((dt, user.decode('utf-8'), text))
				if len(results) == 5:
					break
		if len(results) == 5:
			break
	return results

class ChannelLog:
	def __init__(self, channel_path, date):
		abspath = path.join(config.log_dir, channel_path, date.strftime('%Y-%m-%d'))
		if datetime.datetime.utcnow().date() == date:
			try:
				self.file = open(abspath, 'xb+')
				self.lmi = 0
			except FileExistsError:
				self.lmi = int(_parse(abspath)[0])
				self.file = open(abspath, 'ab+')
			self.compressor = None
		else:
			abspath += '.lz4'
			try:
				self.file = open(abspath, 'xb')
				self.lmi = 0
				contents = None
			except FileExistsError:
				self.lmi, contents = _parse(abspath)
				sefl.lmi = int(self.lmi)
				self.file = open(abspath, 'wb')
			self.compressor = lz4framed.Compressor(self.file)
			if contents:
				self.compressor.update(contents)

		self.date = date

	def log(self, *args, old=False):
		message_id = int(args[0])
		if message_id <= self.lmi:
			if old:
				raise Exception('got message older than last in old log!')
			return
		self.lmi = message_id

		line = '|'.join(args).encode('utf-8') + b'\0'
		if self.compressor:
			self.compressor.update(line)
		else:
			self.file.write(line)
			self.file.flush()

	def close(self):
		if self.compressor:
			self.compressor.end()
			self.file.close()
		elif datetime.datetime.utcnow().date() == self.date:
			self.file.close()
		else:
			self.file.seek(0)
			contents = self.file.read()
			abspath = self.file.name
			self.file.close()
			with open(abspath + '.lz4', 'xb') as f:
				f.write(lz4framed.compress(contents))
			os.unlink(abspath)
