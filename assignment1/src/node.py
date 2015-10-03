import BaseHTTPServer
import sys
import getopt
import time
import threading
import signal
import socket
import httplib
import random
import string
import logging
import httplib
import hashlib
from operator import itemgetter

PORTNR 		 = 8002
direct 		 = dict()
BackendNodes = list()

print "Hello World!"

class StorageServerBackend:

	def __init__(self):
		self.status 	= 200	# Status returned at end of communication.
		self.response 	= ''	# Response message returned at end of communication.
		self.NodesToGet = 1		# Noes to be added to BackendNodes(list).
		self.bitCap 	= 20	# Bit size of truncated key.
		self.successor 	= None	# Next node in the ring.
		self.ValLoad 	= [0,0]	# Key responsibility range.
		self.StoredSize = 0		# Data amount on this node.
		self.nName  = socket.gethostname()	# Name of this node.
		self.DoLogg = True		# Writes to logfile when active.

	# Reduces keysize.
	def truncateKey(self, key):
		returnKey = key % (2**self.bitCap)
		return returnKey

	# Sets up responsibility for the nodes.
	def setup(self):
		if(self.DoLogg):
			for listnode in BackendNodes:
				logging.info('listnode: %s' % listnode)

		# Sorts list by name image.
		# Done to set list in the order of the responsibility ranges.
		BackendNodes.sort(key=itemgetter(0))
		if(self.DoLogg):
			logging.info('sorted')

		# Removes useless info on username.
		if(".local" in self.nName):
			nLen = len(self.nName) -6
			self.nName = self.nName[:nLen]

		# Assigns key responsibility range.
		for listnode in BackendNodes:
			if(listnode[1] == self.nName):
				self.ValLoad[0] = listnode[0]
				nPos = BackendNodes.index(listnode)
				# Successor of the last node in the ring should be the first.
				if(nPos == (len(BackendNodes)-1)):
					self.successor = 0
				else:
					self.successor = nPos +1
			if(self.DoLogg):
				logging.info('listnode: %s' % listnode)
		self.successor 	= BackendNodes[self.successor]
		self.ValLoad[1] = self.successor[0]

		if(self.DoLogg):
			logging.info('successor: %s' % self.successor)
			logging.info('self.ValLoad: %s' % self.ValLoad)

	# Checks if key should be/is a set of this nodes keySpan.
	def responsibilityCheck(self, key):
		# Cheks if current node is the last in the ring.
		if(self.ValLoad[0] > self.ValLoad[1]):
			if(key >= self.ValLoad[0] or key < self.ValLoad[1]):
				return True
			else:
				return False
		else:
			if(key >= self.ValLoad[0] and key < self.ValLoad[1]):
				return True
			else:
				return False

	# Hashes key and reduces its size.
	def hashKey(self, key):
		keyHashed = int(hashlib.sha1(key).hexdigest(), 16)
		keyImage  = self.truncateKey(keyHashed)
		if(self.DoLogg):
			logging.info('keyImage %s' % keyImage)
		return keyImage

	# Return form.
	def packReturn(self):
		if(self.status == 200):
			return [self.status, self.response]
		else:
			return [self.status, None]

	def recvGET(self, key):

		self.status = 200
		if(self.DoLogg):
			logging.info('Enter: do_GET')
			logging.info('key %s' % key)

		# Return info on spaceusage on this node.
		if(key == "/size"):
			self.response = "NODE:" + str(self.nName) + ":\t" + str(self.StoredSize)
			return self.packReturn()

		# Checks if the key is associated whith this node.
		keyImage = self.hashKey(key)
		DoSelf	 = self.responsibilityCheck(keyImage)

		if(self.DoLogg):
			logging.info('post_responsibilityCheck')
			logging.info('direct contain:')
			for entry in direct:
				logging.info('%d' % entry)

		if(DoSelf == True):
			# The key is associated whith this node.
			# Looks for key in directory.
			if direct.has_key(keyImage):
				# The key is pressent in the directory.
				if(self.DoLogg):
					logging.info('there is a key here')
					logging.info('return: %s' % direct.get(keyImage))
				self.response = direct.get(keyImage)
			else:
				# The key is NOT pressent in the directory.
				self.status = 404
				if(self.DoLogg):
					logging.info('that key is not stored here')
		else:
			# The key is NOT associated whith this node.
			# Task is therefore passed to the successor.
			node  = self.successor
			conn2 = httplib.HTTPConnection(node[1], PORTNR)
			conn2.request("GET", key)
			response = conn2.getresponse()
			self.status   = response.status
			self.response = response.read()

			if(self.DoLogg):
				logging.info('passes task')
				logging.info('info passed to: %s' % node[1])

		return self.packReturn()

	def recvPUT(self, key, value):

		# Used to get the addresses of the other nodes.
		if(int(self.NodesToGet) > 0):

			self.NodesToGet = key
			nodeNameHashed 	= int(hashlib.sha1(value).hexdigest(), 16)
			keyImage 		= self.truncateKey(nodeNameHashed)
			BackendNodes.append([keyImage, value])

			# Sets up responsibility for the nodes.
			# Done when all nodes are in BackendNodes(list).
			if((int(self.NodesToGet)+1) == 1):
				self.setup()
				if(self.DoLogg):
					logging.info('nodeAwareness Complete')
					logging.info('')

			if(self.DoLogg):
				logging.info('')
				logging.info('Add nodeAwareness')
				logging.info('NodesToGet: %s' % str(self.NodesToGet))
				logging.info('nodename: %s' % value)
				logging.info('keyImage: %s' % keyImage)

			self.response = "Awareness of " + str(value) + "added"

			return self.packReturn()

		# Checks if the key is associated whith this node.
		keyImage = self.hashKey(key)
		DoSelf   = self.responsibilityCheck(keyImage)

		if(self.DoLogg):
			logging.info('Enter: do_PUT')
			logging.info('key: %s' % key)
			logging.info('responsibilityCheck Done')


		if(DoSelf == True):
			# The key is associated whith this node.
			# Value is stored in directory.
			direct[keyImage] = value

			self.StoredSize += len(direct.get(keyImage))
			response  = "ValueAdded:"
			response += direct.get(keyImage)
			self.status   = 200
			self.response = response

			if(self.DoLogg):
				logging.info('currentSize: %s' % self.StoredSize)
				logging.info('dataAdded: %s' % direct.get(keyImage))
				logging.info('addedOnKey: %s' % keyImage)
				logging.info('response: %s' % response)
		else:
			# The key is NOT associated whith this node.
			# Task is therefore passed to the successor.
			node  = self.successor
			conn2 = httplib.HTTPConnection(node[1], PORTNR)
			conn2.request("PUT", key, value)
			response = conn2.getresponse()
			self.status   = response.status
			self.response = response.read()

			if(self.DoLogg):
				logging.info('passes task')
				logging.info('send to: %s' % node)
				logging.info('response received from: %s' % node[1])
				logging.info('response.status: %s' % self.status)

		return self.packReturn()

class BackendHttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	global backend
	backend = StorageServerBackend()

	def do_GET(self):
		rcv = backend.recvGET(self.path)
		self.send_response(rcv[0])
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(rcv[1])

	def do_PUT(self):
		length 	= int(self.headers['content-length'])
		value 	= self.rfile.read(length)
		rcv = backend.recvPUT(self.path, value)
		self.send_response(rcv[0])
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(rcv[1])

	def sendErrorResponse(self, code, msg):
		self.send_response(code)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(msg)


class BackendHTTPServer(BaseHTTPServer.HTTPServer):

	logging.basicConfig(filename="C" + socket.gethostname()[8:] + ".log",level=logging.DEBUG)

	def server_bind(self):
		BaseHTTPServer.HTTPServer.server_bind(self)
		self.socket.settimeout(1)
		self.run = True

	def get_request(self):
		while self.run == True:
			try:
				sock, addr = self.socket.accept()
				sock.settimeout(None)
				return (sock, addr)
			except socket.timeout:
				if not self.run:
					raise socket.error

	def stop(self):
		self.run = False

	def serve(self):
		while self.run == True:
			self.handle_request()


if __name__ == '__main__':

	# Start the webserver which handles incomming requests
	try:
		httpd = BackendHTTPServer(("",PORTNR), BackendHttpHandler)
		server_thread = threading.Thread(target = httpd.serve)
		server_thread.daemon = True
		server_thread.start()

		def handler(signum, frame):
			print "Stopping http server..."
			httpd.stop()
		signal.signal(signal.SIGINT, handler)

	except:
		print "Error: unable to http server thread"
	# Wait for server thread to exit
	server_thread.join(100)
