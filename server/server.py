# coding=utf-8
#------------------------------------------------------------------------------------------------------
# TDA596 Labs - Server Skeleton
# server/server.py
# Input: Node_ID total_number_of_ID
# Student Group: 99
# Student names: Fredrik Rahn & Alexander Branzell
#------------------------------------------------------------------------------------------------------
# We import various libraries
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler # Socket specifically designed to handle HTTP requests
import sys # Retrieve arguments
import os 	#Folder stuff n folders n shit
from urlparse import parse_qs # Parse POST data
from httplib import HTTPConnection # Create a HTTP connection, as a client (for POST requests to the other vessels)
from urllib import urlencode # Encode POST content into the HTTP header
from codecs import open # Open a file
from threading import  Thread # Thread Management
#------------------------------------------------------------------------------------------------------
#Get correct folder path
file_folder = os.path.dirname(os.path.realpath(__file__)) + '/'
# Global variables for HTML templates
board_frontpage_header_template = open(file_folder + 'board_frontpage_header_template.html', 'r').read()
boardcontents_template = open(file_folder + 'boardcontents_template.html', 'r').read()
entry_template = open(file_folder + 'entry_template.html', 'r').read()
board_frontpage_footer_template = open(file_folder + 'board_frontpage_footer_template.html', 'r').read()
#------------------------------------------------------------------------------------------------------
# Static variables definitions
PORT_NUMBER = 80
#------------------------------------------------------------------------------------------------------
class BlackboardServer(HTTPServer):
#------------------------------------------------------------------------------------------------------
	def __init__(self, server_address, handler, node_id, vessel_list):
		'''
		Init of Blackboard HTTP server
		@args:	server_address:String, Address to Server
				handler:BaseHTTPRequestHandler, Server handler
				node_id:Number, The ID of the node
				vessel_list:[String], list of vessels
		@return:
		'''
		# We call the super init
		HTTPServer.__init__(self,server_address, handler)
		# we create the dictionary of values
		self.store = {}
		# We keep a variable of the next id to insert
		self.current_key = -1
		# our own ID (IP is 10.1.0.ID)
		self.vessel_id = vessel_id
		# The list of other vessels
		self.vessels = vessel_list
#------------------------------------------------------------------------------------------------------
	# We add a value received to the store
	def add_value_to_store(self, value):
		'''
		Adds a new value to store
		@args: Value:String, Value to be added to store
		@return: [Key:String, Value:String]
		'''
		# We add the value to the store
		self.current_key += 1
		key = self.current_key
		if key not in self.store:
			self.store[key]=value
			return [key, value]
		else:
			raise KeyError('Can not add key (Already Exists)')
#------------------------------------------------------------------------------------------------------
	# We modify a value received in the store
	def modify_value_in_store(self, key, value):
		'''
		Modifies value in store
		@args:	Key:Number, 	Key to be modified
				Value:String, 	Value to be added to key
		@return: [Key:Number, Value:String]
		'''
		if key in self.store:								#If Key exists
			self.store[key] = value                         #update key value to value
			return [key, value]
		else:
			raise KeyError('Key does not exist in store')
#------------------------------------------------------------------------------------------------------
	# We delete a value received from the store
	def delete_value_in_store(self,key):
		'''
		Deletes value in store
		@args:	Key:Number, Key to be deleted
		@return: [Key:String]
		'''
		if key in self.store:					#if key exists
			del self.store[key]					#delete entry
		return [key]
#------------------------------------------------------------------------------------------------------
# Contact a specific vessel with a set of variables to transmit to it
	def contact_vessel(self, vessel_ip, path, action, key, value):
		'''
		Handles contact with specific vessel
		@args:	Vessel_ip:String, 	IP to the vessel
				Path:String, 		The path where the request will be sent
				Action:Any, 		Action to be performed
				Key:Number, 		Key for store
				Value:String, 		Value for store
		@return:Entire page:html
		'''
		# the Boolean variable we will return
		success = False
		# The variables must be encoded in the URL format, through urllib.urlencode
		post_content = urlencode({'action': action, 'key': key, 'value': value})
		# the HTTP header must contain the type of data we are transmitting, here URL encoded
		headers = {"Content-type": "application/x-www-form-urlencoded"}
		# We should try to catch errors when contacting the vessel
		try:
			# We contact vessel:PORT_NUMBER since we all use the same port
			# We can set a timeout, after which the connection fails if nothing happened
			connection = HTTPConnection("%s:%d" % (vessel_ip, PORT_NUMBER), timeout = 30)
			# We only use POST to send data (PUT and DELETE not supported)
			action_type = "POST"
			# We send the HTTP request
			connection.request(action_type, path, post_content, headers)
			# We retrieve the response
			response = connection.getresponse()
			# We want to check the status, the body should be empty
			status = response.status
			# If we receive a HTTP 200 - OK
			if status == 200:
				success = True
		# We catch every possible exceptions
		except Exception as e:
			print "Error while contacting %s" % vessel_ip
			# printing the error given by Python
			print(e)

		# we return if we succeeded or not
		return success
#------------------------------------------------------------------------------------------------------
	# We send a received value to all the other vessels of the system
	def propagate_value_to_vessels(self, path, action, key, value):
		'''
		Handles propagation of requests to vessels
		@args:	Path:String,	The path where the request will be sent
				Action:String, 	The action that should be performed by the other vessels
				Key:Number, 	Key that should be used in action
				Value:String, 	Value corresponding to key
		@return:
		'''
		for vessel in self.vessels:
			# We should not send it to our own IP, or we would create an infinite loop of updates
			if vessel != ("10.1.0.%s" % self.vessel_id):
				# A good practice would be to try again if the request failed
				# Here, we do it only once
				self.contact_vessel(vessel, path, action, key, value)
#------------------------------------------------------------------------------------------------------
# This class implements the logic when a server receives a GET or POST
# It can access to the server data through self.server.*
# i.e. the store is accessible through self.server.store
# Attributes of the server are SHARED accross all request hqndling/ threads!
class BlackboardRequestHandler(BaseHTTPRequestHandler):
#------------------------------------------------------------------------------------------------------
	# We fill the HTTP headers
	def set_HTTP_headers(self, status_code = 200):
		'''
		Sets HTTP headers and status code of the response
		@args: Status_code, status code to put in header
		'''
		 # We set the response status code (200 if OK, something else otherwise)
		self.send_response(status_code)
		# We set the content type to HTML
		self.send_header("Content-type","text/html")
		# No more important headers, we can close them
		self.end_headers()
#------------------------------------------------------------------------------------------------------
	# a POST request must be parsed through urlparse.parse_QS, since the content is URL encoded
	def parse_POST_request(self):
		'''
		Parses POST requests
		@args:
		@return: post_data:Dict returns dictionary of URL-encoded data
		'''
		post_data = ""
		# We need to parse the response, so we must know the length of the content
		length = int(self.headers['Content-Length'])
		# we can now parse the content using parse_qs
		post_data = parse_qs(self.rfile.read(length), keep_blank_values=1)
		# we return the data
		return post_data
#------------------------------------------------------------------------------------------------------
# Request handling - GET
#------------------------------------------------------------------------------------------------------
	def do_GET(self):
		'''
		Handles incoming GET requests and routes them accordingly
		'''
		print("Receiving a GET on path %s" % self.path)
		path = self.path[1::].split('/')
		if path[0] == 'board':
			self.do_GET_board()
		elif path[0] == 'entry' and len(path) > 1:
			self.do_GET_entry(path[1])
		else:
			self.do_GET_Index()		#Unknown path, route user to index
#------------------------------------------------------------------------------------------------------
	def do_GET_Index(self):
		'''
		Fetches the Index page and all contents to be displayed
		@return: Entire page:html
		'''
		# We set the response status code to 200 (OK)
		self.set_HTTP_headers(200)

		fetch_index_header = board_frontpage_header_template
		fetch_index_contents = self.board_helper()
		fetch_index_footer = board_frontpage_footer_template

		html_response = fetch_index_header + fetch_index_contents + fetch_index_footer

		self.wfile.write(html_response)
#------------------------------------------------------------------------------------------------------
	def board_helper(self):
		'''
		Helper func for fetching board contents
		@return: List of boardcontents
		'''
		fetch_index_entries = ""
		for entryId, entryValue in self.server.store.items():
			fetch_index_entries += entry_template %("entries/" + str(entryId), entryId, entryValue)
		boardcontents = boardcontents_template % ("Title", fetch_index_entries)
		return boardcontents
#------------------------------------------------------------------------------------------------------
	def do_GET_board(self):
		'''
		Fetches the board and its contents
		'''
		self.set_HTTP_headers(200)
		html_response = self.board_helper()
		self.wfile.write(html_response)
#------------------------------------------------------------------------------------------------------
	def do_GET_entry(self, entryID):
		'''
		Retrieve an entry from store and inserts it into the entry_template
		@args: entryID:String, ID of entry to be retrieved
		@return: Entry:html
		'''
		#Find the specific value for the entry, if entry does not exist set value to None
		entryValue = self.server.store[entryId] if entryId in self.server.store else None
		#Return found entry if it exists, or return empty string if no such entry was found
		return entry_template %("entries/" + entryId, entryId, entryValue) if entryValue != None else ""
#------------------------------------------------------------------------------------------------------
# Request handling - POST
#------------------------------------------------------------------------------------------------------
	def do_POST(self):
		'''
		Handles incoming POST requests and routes them accordingly
		'''
		print("Receiving a POST on %s" % self.path)
		path = self.path[1::].split('/')
		if path[0] == 'board' and len(path) < 2:
			self.do_POST_board()
		elif path[0] == 'entries' and len(path) > 1:
			self.do_POST_entries(path[1])
		elif path[0] == 'propagate':
			self.do_POST_propagate()
#------------------------------------------------------------------------------------------------------
	def do_POST_board(self):
		'''
		Add entries to board
		'''
		post_data = self.parse_POST_request()
		if 'entry' in post_data:
			value = post_data['entry'][0]
			entry = self.do_POST_add_entry(value)
			self.propagate_action(action='add', key=entry[0], value=entry[1])
		else:
			self.send_error(400, 'Error adding entry to board')
#------------------------------------------------------------------------------------------------------
	def do_POST_entries(self, entryID):
		'''
		Handles deleting and modifying entries to the board
		@args: entryID:String, ID of entry to be modified/deleted
		'''
		post_data = self.parse_POST_request()
		if 'delete' in post_data:
			delete = post_data['delete'][0]
			if delete == '1':
				entry = self.do_POST_delete_entry(int(entryID))
				self.propagate_action(action='delete', key=entry[0])
			else:
				modified_value = post_data['entry'][0]
				entry = self.do_POST_modify_entry(int(entryID), modified_value)
				self.propagate_action(action='modify', key=entry[0], value=entry[1])
		else:
			self.send_error(400, 'Delete flag missing from request')
#------------------------------------------------------------------------------------------------------
	def do_POST_propagate(self):
		'''
		Handles propagation of actions by
		routing them to the correct functions
		'''
		post_data = self.parse_POST_request()
		if 'action' in post_data:
			action = post_data['action'][0]
			value = post_data['value'][0]
			key = post_data['key'][0]
			if action == 'add':
				self.do_POST_add_entry(value)
			elif action == 'modify':
				self.do_POST_modify_entry(key, value)
			elif action == 'delete':
				self.do_POST_delete_entry(key)
			else:
				self.send_error(400, 'Invalid action')
#------------------------------------------------------------------------------------------------------
	def do_POST_add_entry(self, value):
		'''
		Adds a new entry to store
		@args: value:Value, Value to be added in store
		@return: entry:List, [key, value]
		'''
		entry = self.server.add_value_to_store(value=value)
		if entry:
			self.send_response(200)
			return entry
		else:
			self.send_error(400, "Value was not added.")
#------------------------------------------------------------------------------------------------------
	def do_POST_modify_entry(self, entryID, value):
		'''

		Modifies a specific entry in store
		@args: entryID:String, ID of entry to be modified
		@args: value:String, new value to be assigned to entryID
		@return: entry:List, [key, value]
		'''
		entry = self.server.modify_value_in_store(int(entryID), value)
		if entry:
			self.send_response(200)
			return entry
		else:
			 self.send_error(400, 'Entry not modified')
#------------------------------------------------------------------------------------------------------
	def do_POST_delete_entry(self, entryID):
		'''
		Deletes an entry in store
		@args: entryID:String
		@return: entry:List, [key]
		'''
		entry = self.server.delete_value_in_store(int(entryID))
		if entry and entryID != None:
			self.send_response(200)
			return entry
		else:
			 self.send_error(400, 'Entry not deleted')
#------------------------------------------------------------------------------------------------------
	def propagate_action(self, action, key='', value=''):
		'''
		Spawns a thread and propagates an action to other vessels
		@args: action:String
		@args: key:String
		@args: value:String
		'''
		propagate_path = '/propagate'
		print('path, action, key, value', propagate_path, action, key, value)
		thread = Thread(target=self.server.propagate_value_to_vessels, args=(propagate_path, action, key, value))
		print('tried to propagate')

		# We kill the process if we kill the serverx
		thread.daemon = True
		# We start the thread
		thread.start()
#------------------------------------------------------------------------------------------------------
# Execute the code
if __name__ == '__main__':

	## read the templates from the corresponding html files
	# .....

	vessel_list = []
	vessel_id = 0
	# Checking the arguments
	if len(sys.argv) != 3: # 2 args, the script and the vessel name
		print("Arguments: vessel_ID number_of_vessels")
	else:
		# We need to know the vessel IP
		vessel_id = int(sys.argv[1])
		# We need to write the other vessels IP, based on the knowledge of their number
		for i in range(1, int(sys.argv[2])+1):
			vessel_list.append("10.1.0.%d" % i) # We can add ourselves, we have a test in the propagation

	# We launch a server
	server = BlackboardServer(('', PORT_NUMBER), BlackboardRequestHandler, vessel_id, vessel_list)
	print("Starting the server on port %d" % PORT_NUMBER)

	try:
		server.serve_forever()
	except KeyboardInterrupt:
		server.server_close()
		print("Stopping Server")
#------------------------------------------------------------------------------------------------------
