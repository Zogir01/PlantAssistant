# This file is based on the original file "server.py" from the project:
#
# "K-ESP-CTRL" by Kuszki
#   https://github.com/Kuszki/K-ESP-CTRL
#
# Original code copyright: (c) 2021 Kuszki.
# Licensed under the GNU General Public License v3.0
#

# coding=UTF-8

import socket, select, json, gc
from binascii import a2b_base64, hexlify
from micropython import const
from hashlib import sha1

class HttpServer:

	def __init__(self, port = 80):

		try: self.users = json.load(open('/etc/users.json', 'r'))
		except: self.users = dict()

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(('', port))
		self.sock.listen(25)

		self.poll = select.poll()
		self.poll.register(self.sock, select.POLLIN)

		self.slites = dict()

	def accept(self):

		if self.poll.poll(0):

			try: s = self.sock.accept()[0]
			except: return None
			else: s.settimeout(3)

			try: self.recv(s)
			except: pass
			else: gc.collect()
			finally: s.close()

	def recv(self, sock):

		try:

			try: buff = sock.recv(1024)
			except: return None

			while buff.find(b'\r\n\r\n') == -1:
				if not buff: raise BufferError
				else: buff += sock.recv(1024)

			if not self.auth(buff):
				code = b'401 Unauthorized'
				slite = None

			elif buff.startswith(b'GET /'):
				slite, par = self.get(buff, sock)

			elif buff.startswith(b'POST /'):
				slite, par = self.post(buff, sock)

			else:
				code = b'405 Method Not Allowed'
				slite = None

			del buff; gc.collect()

			if slite: code = self.resp(slite, par, sock)

			if code: sock.sendall(\
				b'HTTP/1.1 %s\r\n' \
				b'Allow: GET, POST\r\n' \
				b'Connection: close\r\n' \
				b'Content-Length: %s\r\n' \
				b'WWW-Authenticate: Basic\r\n' \
				b'Accept: application/json\r\n' \
				b'text/plain; charset=utf-8\r\n' \
				b'Access-Control-Allow-Origin: *\r\n' \
				b'\r\n%s' % (code, len(code), code))
		# zmiana: dodanie Access-Control-Allow-Origin, - każdy może odczytać zasób / obejście zabezpieczenia CORS w przeglądarce /Zogir

		except: raise
		finally: gc.collect()

	def resp(self, slite, par, sock):

		con = mim = siz = res = None

		if slite in self.slites:
			# try: con = self.slites[slite](par)
			# except: return b'406 Not Acceptable'
			try: con = self.slites[slite](par)
			except Exception as e: 
				# tylko w ramach testów - w przysżłości przywrócić wcześniejszą wersje 		/Zogir
				print(e)
				return b'406 Not Acceptable'

		else:
			try: res, mim, siz = self.slite(slite)
			except: return b'404 Not Found'

		if res == None: res = str(con).encode()
		if mim == None: mim = self.mime(slite)
		if siz == None: siz = len(res)

		try:

			sock.sendall(\
				b'HTTP/1.1 200 OK\r\n' \
				b'Content-Type: %s\r\n' \
				b'Connection: close\r\n' \
				b'Content-Length: %s\r\n' \
				b'Access-Control-Allow-Origin: *\r\n' \
				b'\r\n' % (mim, siz))
			sock.sendall(res)
		# zmiana: dodanie Access-Control-Allow-Origin, - każdy może odczytać zasób / obejście zabezpieczenia CORS w przeglądarce /Zogir

		except: raise
		finally: del res

	def get(self, req, sock):

		e = req.find(b'\r\n')
		a = req.find(b'GET /', 0, e) + 5
		b = req.find(b' HTTP', a, e)

		if a == 4 or b == -1 or a > b:
			return str(), dict()
		else: req = req[a:b]

		par = req.find(b'?')
		d = self.unquote

		if par != -1:

			slite = d(req[0:par])
			req = req[par+1:]
			vlist = self.split(req)

		else:

			slite = d(req)
			vlist = dict()

		if slite == b'': slite = 'index.html'
		else: slite = slite.decode()

		return slite, vlist

	def post(self, req, sock):

		e = req.find(b'\r\n')
		a = req.find(b'POST /', 0, e) + 6
		b = req.find(b' HTTP', a, e)
		e = req.find(b'\r\n\r\n', e)
		d = self.unquote

		if a == 5 or b == -1 or a > b:
			return str(), dict()

		elif a == b: slite = 'index.html'
		else: slite = d(req[a:b]).decode()

		j = req.find(b'Content-Type: application/json', b, e)
		p = req.find(b'Content-Type: text/plain', b, e)
		a = req.find(b'Content-Length: ', b, e) + 15
		b = req.find(b'\r\n', a, e)

		if a == 14 or b == -1 or a > b:
			return slite, dict()

		else:
			try: leng = int(req[a:b])
			except: return slite, dict()
			else: req = req[e+4:]

		while len(req) != leng:
			try: req += sock.recv(leng - len(req))
			except: return slite, dict()
			if not req: raise BufferError

		if j != -1: vlist = json.loads(req)
		elif p != -1: vlist = req.decode()
		else: vlist = self.split(req)

		return slite, vlist

	def auth(self, req):

		if not len(self.users): return True

		s = req.find(b'\r\n') + 2
		e = req.find(b'\r\n\r\n')
		a = req.find(b'Authorization: Basic ', s, e) + 21
		b = req.find(b'\r\n', a)

		if a == 20 or b == -1 or a > b: return False
		else: auth = a2b_base64(req[a:b]).split(b':')

		if len(auth) != 2: return False
		else:
			u = auth[0].decode()
			p = auth[1].decode()

		if not u in self.users: return False
		else:
			h = hexlify(sha1(p).digest())
			ok = self.users[u] == h.decode()

		return ok

	def unquote(self, string):

		if not string: return bytes()
		if not b'%' in string: return string

		bits = string.split(b'%')
		res = [ bits[0] ]

		for s in bits[1:]:

			try:

				char = bytes([int(s[:2], 16)])
				res.append(char)
				res.append(s[2:])

			except:

				res.append(b'%')
				res.append(s)

		return b''.join(res)

	def split(self, string):

		d = self.unquote
		vlist = dict()

		for p in string.split(b'&'):

			if p.find(b'=') != -1:

				i = p.split(b'=')
				k = d(i[0]).decode()
				v = d(i[1]).decode()

				vlist[k] = v

			else:

				k = d(p).decode()
				vlist[k] = None

		return vlist

	# def slite(self, path):

	# 	if path == 'favicon.ico': path = '/obj/favicon.ico'

	# 	elif path.endswith('.html'): path = '/http/%s' % path
	# 	elif path.endswith('.json'): path = '/etc/%s' % path
	# 	elif path.endswith('.css'): path = '/css/%s' % path
	# 	elif path.endswith('.js'): path = '/src/%s' % path

	# 	else: path = '/var/%s' % path

	# 	try:

	# 		with open(path, 'rb') as f:

	# 			mime = self.mime(path)
	# 			cont = f.read()
	# 			size = len(cont)

	# 	except: raise
	# 	else: return cont, mime, size

	def slite(self, path):

		if path == 'favicon.ico': path = '/web/assets/favicon.ico'
		elif path.endswith('.html'): path = '/web/%s' % path
		# elif path.endswith('.json'): path = '/config/%s' % path
		elif path.endswith('.css'): path = '/web/css/%s' % path
		elif path.endswith('.js'): path = '/web/js/%s' % path

		else: path = '/var/%s' % path

		try:

			with open(path, 'rb') as f:

				mime = self.mime(path)
				cont = f.read()
				size = len(cont)

		except: raise
		else: return cont, mime, size

	def mime(self, path):

		if path.startswith('/var/'): mime = b'application/json'
		elif path.endswith('.html'): mime = b'text/html'
		elif path.endswith('.json'): mime = b'application/json'
		elif path.endswith('.css'): mime = b'text/css'
		elif path.endswith('.ico'): mime = b'image/png'
		elif path.endswith('.js'): mime = b'text/javascript'

		else: mime = b'text/plain'

		return b'%s; charset=utf-8' % mime

	def defslite(self, slite, callback):

		self.slites[slite] = callback

	def rmslite(self, slite):

		del self.slites[slite]
