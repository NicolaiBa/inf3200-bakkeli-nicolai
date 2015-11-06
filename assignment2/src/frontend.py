import BaseHTTPServer
import threading
import signal
import socket
import httplib
import random
import os
import time

PORTNR = 8020

httpdServeRequests  = True
ServerActive = False

class StorageServerFrontend:

	def __init__(self):
		self.size = 0
		self.portnumber = PORTNR
		self.CWD = os.path.dirname(os.path.realpath(__file__))
		self.testdir = self.CWD + "/tests"
		self.nodedir = self.CWD + "/nodes"

	def sendGET(self, key):
		if(key == "/ElectionTest"):
			if not os.path.exists(self.testdir):
				os.makedirs(self.testdir)

		activenodes = len(os.listdir(self.nodedir))
		if activenodes > 0:
			node = random.choice(os.listdir(self.nodedir))[:-4]
			print "Node used: ", node
		else:
			return "No nodes are active"

		if(key == "/ElectionTest"):

			conn = httplib.HTTPConnection(node, PORTNR)
			conn.request("GET", key)
			response = conn.getresponse()

			resp = response.read()
			indx = resp.index(":")
			ElTime = resp[:indx]
			NodesCount = resp[indx+1:]
			print "ElTime: ", ElTime
			print "NodesCount: ", NodesCount
			print resp

			self.testfile = self.testdir+"/"+str(NodesCount)+".txt"

			print "self.testfile", self.testfile

			if not os.path.isfile(self.testfile):
				file = open(self.testfile, 'w')
				file.close()
			file = open(self.testfile, 'a')

			if(ElTime != "False"):
				file.write(str(ElTime)+"\n")
			file.close()

			if response.status != 200:
				print response.reason
				return "Incorrect response"

		else:
			conn = httplib.HTTPConnection(node, PORTNR)
			conn.request("GET", key)
			response = conn.getresponse()
			resp = response.read()

		return resp

	def sendPUT(self, key, value, size):

		# Outputs amount og data stored at the backend nodes
		self.size = self.size + size
		if len(os.listdir(self.nodedir)) > 0:
			node = random.choice(os.listdir(self.nodedir))[:-4]
			print "Node used: ", node
		else:
			return "No nodes are active"

		print "PUT key:", key
		print "PUT value:", value
		print "PUT new size:", self.size
		print "PUT added size:", size

		conn = httplib.HTTPConnection(node, self.portnumber)
		conn.request("PUT", key, value)
		response = conn.getresponse()

		print "data: " + response.read()
		return response.read()


class FrontendHttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	global frontend
	frontend = StorageServerFrontend()

	# Returns the
	def do_GET(self):
		key = self.path
		value = frontend.sendGET(key)

		if value is None:
			self.sendErrorResponse(404, "Key not found")
			return

		# Write header
		self.send_response(200)
		self.send_header("Content-type", "application/octet-stream")
		self.end_headers()

		# Write Body
		self.wfile.write(value)

	def do_PUT(self):
		contentLength = int(self.headers['Content-Length'])

		# Forward the request to the backend servers
		frontend.sendPUT(self.path, self.rfile.read(contentLength), contentLength)

		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def sendErrorResponse(self, code, msg):
		self.send_response(code)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(msg)

class FrontendHTTPServer(BaseHTTPServer.HTTPServer):

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
		global ServerActive
		ServerActive = True
		while self.run == True:
			self.handle_request()
		ServerActive = False


if __name__ == '__main__':

	print "PORTNR: ", PORTNR

	httpserver_port = PORTNR

	# Start the webserver which handles incomming requests
	try:
		httpd = FrontendHTTPServer(("",httpserver_port), FrontendHttpHandler)
		server_thread = threading.Thread(target = httpd.serve)
		server_thread.daemon = True
		server_thread.start()

		def handler(signum, frame):
			print "Stopping http server..."
			httpd.stop()
			global ServerActive
			while(ServerActive == True):
				time.sleep(0.001)
			server_thread.join(0.1)
		signal.signal(signal.SIGINT, handler)

	except:
		print "Error: unable to http server thread"

	# Wait for server thread to exit

	while server_thread.isAlive():
		time.sleep(0.01)
