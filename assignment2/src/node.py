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
import hashlib
from operator import itemgetter
import os

PORTNR 		 = 8020
ServerActive = False

Navn  = socket.gethostname()	# Name of this node.
# Removes useless info on username.
if(".local" in Navn):
	nLen = len(Navn) -6
	Navn = Navn[:nLen]

class Bully():

	def __init__(self):
		self.active      = True		# Thread runs until active is False.
		self.vitCheck	 = False	# Initializes node vitality control.
		self.vitList 	 = False	# Used to list vital nodes.
		self.TimeVicWait = 2		# Max time spent waiting for the new coordinator.
		self.TimeCoorVit = 5		# Time between coordinator checks.
		self.contender   = False	# Used to figure out if this node should be coordinator.
		self.coordinator = False	# Coordinator state.
		self.slave       = False	# Slave state.
		self.workReady   = False	# Thread is ready for work.
		self.coordiname  = False	# Name of Coordinator.
		self.filename    = False	# File named after node address.
		self.connections = []		# List of open connections.
		self.Nodes		 = list()	# List of known nodes.
		self.dirname = os.path.dirname(os.path.realpath(__file__)) + "/nodes"
		self.nName  = socket.gethostname()	# Name of this node.
		# Removes useless info on username.
		if(".local" in self.nName):
			nLen = len(self.nName) -6
			self.nName = self.nName[:nLen]
		return

	def startUp(self):
		"""	Creates file named after itself. """
		#Makes sure there is a node-dictionay.
		if not os.path.exists(self.dirname):
			os.makedirs(self.dirname)

		#Adds nodename to directory.
		self.filename = self.dirname+"/"+self.nName+".txt"
		file = open(self.filename, 'w')
		file.close()

	def integrate(self):
		""" Finds other nodes in the network from the 'node' dictionary. """
		nodeCount = str(len(os.listdir(self.dirname))-1)
		for node in os.listdir(self.dirname):
			#Removes ".txt"
			activeNode = node[:-4]
			self.Nodes.append([activeNode, False])
		self.workReady = True

	def readyBroadcast(self):
		"""
		Broadcast a message to every other known node,
		signaling that this node is ready.
		"""
		del self.connections[:]
		for listnode, ready in self.Nodes:
			conn = httplib.HTTPConnection(listnode, PORTNR)
			try:
				conn.request("PUT", "ready", self.nName)
				response = conn.getresponse()
				if(response.read() == "ready"):
					indx = self.Nodes.index([listnode, ready])
					self.Nodes[indx] = [listnode, True]
				conn.close()
			except:
				conn.close()
				continue

	def readyReceive(self):
		"""
		Waits and receives messages from other nodes.
		This continues until every other node is known to be ready.
		"""
		waiting = True
		while(waiting and self.workReady):
			allReady = True
			for listnode, ready in self.Nodes:
				if not ready:
					conn = httplib.HTTPConnection(listnode, PORTNR)
					try:
						conn.request("PUT", "ready", self.nName)
						response = conn.getresponse()
						if(response.read() == "ready"):
							indx = self.Nodes.index([listnode, ready])
							self.Nodes[indx] = [listnode, True]
					except:
						time.sleep(0.0001)
					conn.close()

					allReady = False
					break
			if allReady:
				waiting = False

	def shutDown(self):
		"""
		Run to close things down.
		Destroys the file named after itself,
		signals every other node that it is shuting down.
		"""
		if os.path.isfile(self.filename):
			os.remove(self.filename)

		del self.connections[:]
		for listnode, ready in self.Nodes:
			if listnode != self.nName:
				conn = httplib.HTTPConnection(listnode, PORTNR)
				try:
					conn.request("PUT", "senderShutDown", self.nName)
					self.connections.append([conn, listnode])
				except:
					time.sleep(0.000001)
					continue

		for conn, listnode in self.connections:
			try:
				response = conn.getresponse()
				conn.close()
			except:
				conn.close()
				continue

		self.workReady = False

	def vitBroadcast(self):
		"""
		Run to check if nodes are alive.
		Nodes that are alive are added to vitList.
		"""
		del self.connections[:]

		self.vitList = socket.gethostbyname(self.nName) + ":" + str(PORTNR) + "\n"

		for listnode, ready in self.Nodes:
			if listnode != self.nName:
				conn = httplib.HTTPConnection(listnode, PORTNR, timeout=0.1)
				try:
					conn.request("GET", "vitality")
					self.connections.append([conn, listnode])
				except:
					conn.close()
					continue

		testlist = []
		for conn, listnode in self.connections:
			try:
				response = conn.getresponse()
				if (response.status == 200):
					resultString = response.read()
					self.vitList = self.vitList + resultString
					testlist.append(resultString)
				conn.close()
			except:
				conn.close()
				continue

		self.vitCheck = False

	def electionBroadcast(self):
		"""
		Run to inform other nodes that the election is starting.
		Fingures if self is supposed to be coordinator.
		"""

		del self.connections[:]
		for listnode, ready in self.Nodes:
			if listnode > self.nName:
				conn = httplib.HTTPConnection(listnode, PORTNR)
				try:
					conn.request("GET", "election")
					self.connections.append([conn, listnode])
				except:
					conn.close()
					continue

		self.contender = True

		for conn, listnode in self.connections:
			try:
				response = conn.getresponse()
				if (response.status == 200):
					self.contender = False
				conn.close()
			except:
				conn.close()
				continue

		self.coordinator = self.contender
		self.newBoss     = self.contender
		self.slave   = not self.contender
		if self.coordinator:
			self.coordiname = self.nName

	def victoryBroadcast(self):
		"""
		Run to signal other nodes to tell them that this node is the new coordinator.
		"""
		del self.connections[:]
		for listnode, ready in self.Nodes:
			conn = httplib.HTTPConnection(listnode, PORTNR)
			try:
				conn.request("PUT", "nCoordinator", self.nName)
				self.connections.append([conn, listnode])
			except:
				conn.close()
				continue

		for conn, listnode in self.connections:
			try:
				response = conn.getresponse()
				conn.close()
			except:
				conn.close()
				continue

		self.newBoss = False

	def waitForVictor(self):
		"""
		Waits for the new coordinator.
		"""
		start_time = time.time()
		while((time.time() - start_time) < self.TimeVicWait):
			if(self.coordiname != False):
				break

		if(self.coordiname == False):
			self.slave = False

	def checkCoordinator(self):
		"""
		Checks if current coordinator is still alive.
		"""
		conn = httplib.HTTPConnection(self.coordiname, PORTNR)
		try:
			conn.request("GET", "mastervit")
			response = conn.getresponse()
			if (response.status != 200):
				self.coordiname = False
				self.slave = False
			conn.close()
		except:
			conn.close()
			self.coordiname = False
			self.slave = False

	def run(self):
		"""
		Main loop of bully_thread.
		"""
		self.startUp()
		self.integrate()
		self.readyBroadcast()
		self.readyReceive()

		start_time = time.time()
		while(self.active):
			looped_time = time.time()

			if(self.coordinator == False and self.slave == False):
				self.electionBroadcast()

			elif(self.coordinator == True and self.newBoss == True):
				self.victoryBroadcast()

			if(self.slave == True and self.coordiname == False):
				self.waitForVictor()

			elif(self.slave == True and self.coordiname != False):
				if((looped_time - start_time) >= self.TimeCoorVit):
					self.checkCoordinator()
					start_time = time.time()

			if(self.vitCheck):
				self.vitBroadcast()

		self.shutDown()

class StorageServerBackend:

	def __init__(self):
		self.status 	= 200	# Status returned at end of communication.
		self.response 	= ''	# Response message returned at end of communication.
		self.NodesToGet = 1		# Noes to be added to Nodes(list).
		self.DoLogg = True		# Writes to logfile when active.
		self.nName  = socket.gethostname()	# Name of this node.
		self.coordinator = False
		self.electionTime = False
		self.electionTimeStart = False
		self.tester = False
		self.nodesAtElection = False
		# Removes useless info on username.
		if(".local" in self.nName):
			nLen = len(self.nName) -6
			self.nName = self.nName[:nLen]
		global bt

	# Return form.
	def packReturn(self):
		if(self.status == 200):
			return [self.status, self.response]
		else:
			return [self.status, False]

	def recvGET(self, key):

		self.status = 404
		self.response = False

		if(key == "mastervit"):
			"""
			A slave asks if this node (current coordinator) is stil alive.
			"""
			self.status = 200
			self.response = "alive"

		if(key == "election"):
			"""
			Another node have noticed that it is time for a coordinator election.
			"""
			self.status = 200
			self.response = "alive"
			bt.slave = False
			bt.coordinator = False
			bt.coordiname = False

		elif(key == "vitality"):
			"""
			The node is asked if it is alive.
			Response is used to create the list as a response to "/getNodes".
			"""
			self.status   = 200
			self.response = socket.gethostbyname(self.nName)+":"+str(PORTNR)+"\n"

		elif(key == "/getCurrentLeader"):
			"""
			The user wishes to know the current coordinator
			"""
			self.status   = 200
			# Waits until the leader is selected.
			while(bt.coordiname == False):
				time.sleep(0.1)
			self.response = socket.gethostbyname(bt.coordiname)+":"+str(PORTNR)

		elif(key == "/getNodes"):
			"""
			The user want a list of active nodes.
			"""
			self.status = 200
			bt.vitCheck = True
			while(bt.vitCheck == True):
				time.sleep(0.1)
			self.response = bt.vitList

		elif(key == "/ElectionTest"):
			"""
			Used for election time testing.
			"""
			self.response = str(self.electionTime)+":"+str(self.nodesAtElection)
			self.electionTimeStart = time.time()
			self.tester = True
			self.status = 200

			bt.coordinator = False
			bt.coordiname = False
			bt.slave = False

		return self.packReturn()

	def recvPUT(self, key, value):

		self.status = 200
		self.response = False

		if(key == "nCoordinator"):
			"""
			The new coordinator has been chosen.
			"""
			self.status = 200
			self.response = "right"
			self.coordinator = value
			bt.coordiname = value
			if self.tester:
				self.nodesAtElection = len(bt.Nodes)
				self.electionTime = time.time() - self.electionTimeStart
				self.tester = False

		elif(key == "ready"):
			"""
			Another node claim to be ready for work.
			Updates own table to itegrate new node.
			"""
			self.status = 200
			self.response = "right"
			Added = False

			if [value, True] in bt.Nodes:
				indx = bt.Nodes.index([value, True])
				bt.Nodes[indx] = [value, True]

			elif [value, False] in bt.Nodes:
				indx = bt.Nodes.index([value, False])
				bt.Nodes[indx] = [value, True]
			else:
				bt.Nodes.append([value, True])
			self.response = "ready"

		elif(key == "senderShutDown"):
			"""
			The sender is shuting down.
			Sender is removed from table.
			"""
			self.status = 200
			self.response = "right"

			if [value, True] in bt.Nodes:
				indx = bt.Nodes.index([value, True])
				bt.Nodes.pop(indx)

			elif [value, False] in bt.Nodes:
				indx = bt.Nodes.index([value, False])
				bt.Nodes.pop(indx)

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

	def server_bind(self):
		BaseHTTPServer.HTTPServer.server_bind(self)
		self.socket.settimeout(1)
		self.run = True

	def get_request(self):
		while self.run == True:
			try:
				sock, addr = self.socket.accept()
				sock.settimeout(False)
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
			try:
				self.handle_request()
			except Exception, e:
				e = sys.exc_info()[0]
				continue
		ServerActive = False

if __name__ == '__main__':

	# Start the webserver which handles incomming requests
	httpd = BackendHTTPServer(("",PORTNR), BackendHttpHandler)
	server_thread = threading.Thread(target = httpd.serve)
	server_thread.daemon = True
	server_thread.start()

	bt = Bully()
	bully_thread = threading.Thread(target = bt.run)
	bully_thread.daemon = True
	bully_thread.start()

	def handler(signum, frame):
		bt.active = False
		while(bt.workReady == True):
			time.sleep(0.001)

		httpd.stop()
		global ServerActive
		while(ServerActive == True):
			time.sleep(0.001)

		bully_thread.join(0.01)
		server_thread.join(0.01)

	signal.signal(signal.SIGINT, handler)
	signal.signal(signal.SIGTERM, handler)

	while server_thread.isAlive() or bully_thread.isAlive():
		time.sleep(0.01)
