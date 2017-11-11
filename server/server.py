# coding=utf-8
#------------------------------------------------------------------------------------------------------
# TDA596 Labs - Server Skeleton
# server/server.py
# Input: Node_ID total_number_of_ID
# Student Group:
# Student names: John Doe & John Doe
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




#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class BlackboardServer(HTTPServer):
#------------------------------------------------------------------------------------------------------
	def __init__(self, server_address, handler, node_id, vessel_list):
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
		# We add the value to the store
		self.current_key+=1
		self.store[self.current_key]=value
		return self.store[self.current_key] == value           #If value exists on correct key, return True

#------------------------------------------------------------------------------------------------------
	# We modify a value received in the store
	def modify_value_in_store(self,key,value):
		if key in self.store:								#If Key exists
			self.store[key] = value                         #update key value to value
			return self.store[key] == value					#return True if key has succesfully been modified
		return False                                        #return False if key does not exist
#------------------------------------------------------------------------------------------------------
	# We delete a value received from the store
	def delete_value_in_store(self,key):
		if key in self.store:					#if key exists
			del self.store[key]					#delete entry
        	return True
		return False                            #return False if key does not exist
#------------------------------------------------------------------------------------------------------
# Contact a specific vessel with a set of variables to transmit to it
	def contact_vessel(self, vessel_ip, path, action, key, value):
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
		# We iterate through the vessel list
		for vessel in self.vessels:
			# We should not send it to our own IP, or we would create an infinite loop of updates
			if vessel != ("10.1.0.%s" % self.vessel_id):
				# A good practice would be to try again if the request failed
				# Here, we do it only once
				self.contact_vessel(vessel, path, action, key, value)
#------------------------------------------------------------------------------------------------------







#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# This class implements the logic when a server receives a GET or POST request
# It can access to the server data through self.server.*
# i.e. the store is accessible through self.server.store
# Attributes of the server are SHARED accross all request hqndling/ threads!
class BlackboardRequestHandler(BaseHTTPRequestHandler):
#------------------------------------------------------------------------------------------------------
	# We fill the HTTP headers
	def set_HTTP_headers(self, status_code = 200):
		 # We set the response status code (200 if OK, something else otherwise)
		self.send_response(status_code)
		# We set the content type to HTML
		self.send_header("Content-type","text/html")
		# No more important headers, we can close them
		self.end_headers()
#------------------------------------------------------------------------------------------------------
	# a POST request must be parsed through urlparse.parse_QS, since the content is URL encoded
	def parse_POST_request(self):
		post_data = ""
		# We need to parse the response, so we must know the length of the content
		length = int(self.headers['Content-Length'])
		# we can now parse the content using parse_qs
		post_data = parse_qs(self.rfile.read(length), keep_blank_values=1)
		# we return the data
		return post_data
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# Request handling - GET
#------------------------------------------------------------------------------------------------------
	# This function contains the logic executed when this server receives a GET request
	# This function is called AUTOMATICALLY upon reception and is executed as a thread!
	def do_GET(self):
		print("Receiving a GET on path %s" % self.path)
		# Here, we should check which path was requested and call the right logic based on it
		self.do_GET_path()
#------------------------------------------------------------------------------------------------------
# GET logic - specific path
#Implement /board
#Implement /entry/entryID
	def do_GET_path(self):
		path = self.path[1::].split('/')
		if path[0] == 'board':
			self.do_GET_board()
		elif path[0] == 'entry' and len(path) > 1:
			self.do_GET_entry(path[1])
		else:
			self.do_GET_Index()		#Unknown path, route user to index
#------------------------------------------------------------------------------------------------------
	'''
	View the board's contents
	@args:
	@return: Entire page:html
	'''
	def do_GET_Index(self):
		# We set the response status code to 200 (OK)
		self.set_HTTP_headers(200)

		fetch_index_header = board_frontpage_header_template
		fetch_index_contents = self.board_helper()
		fetch_index_footer = board_frontpage_footer_template

		# We should do some real HTML here
		html_response = fetch_index_header + fetch_index_contents + fetch_index_footer
		#In practice, go over the entries list,
		#produce the boardcontents part,
		#then construct the full page by combining all the parts ...

		self.wfile.write(html_response)
#------------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------------
	'''
	Helper func for fetching board contents
	@args:
	@return: List of entries
	'''
	def board_helper(self):
		fetch_index_entries = ""
		for entryId, entryValue in self.server.store.items():
			fetch_index_entries += entry_template %("entries/" + str(entryId), entryId, entryValue)
		boardcontents = boardcontents_template % ("Title", fetch_index_entries)
		return boardcontents
#------------------------------------------------------------------------------------------------------
	'''
	Fetches board
	@args:
	@return: Board
	'''
	def do_GET_board(self):
		self.set_HTTP_headers(200)
		html_response = self.board_helper()
		self.wfile.write(html_response)

#------------------------------------------------------------------------------------------------------
	'''
	Retrieve entry
	@args:
	@return: Entry:html
	'''
	def do_GET_entry(entryID):
		#Find the specific value for the entry, if entry does not exist set value to None
		entryValue = self.server.store[entryId] if entryId in self.server.store else None
		#Return found entry if it exists, or return empty string if no such entry was found
		return entry_template %("entries/" + entryId, entryId, entryValue) if entryValue != None else ""

#------------------------------------------------------------------------------------------------------
# Request handling - POST
#------------------------------------------------------------------------------------------------------
	def do_POST(self):
		print("Receiving a POST on %s" % self.path)
		# Here, we should check which path was requested and call the right logic based on it
		# We should also parse the data received
		# and set the headers for the client

		self.do_POST_path()			#Call router for pathing

		# If we want to retransmit what we received to the other vessels
		retransmit = False # Like this, we will just create infinite loops!
		if retransmit:
			# do_POST send the message only when the function finishes
			# We must then create threads if we want to do some heavy computation
			#
			# Random content
			thread = Thread(target=self.server.propagate_value_to_vessels,args=("action", "key", "value") )
			# We kill the process if we kill the server
			thread.daemon = True
			# We start the thread
			thread.start()
#------------------------------------------------------------------------------------------------------
# POST Logic
#Implement POST /entries					#Add a new entry
#Implement POST /entries/entryID			#Delete an entry
	def do_POST_path(self):
		path = self.path[1::].split('/')
		if path[0] == 'board' and len(path) < 2:
			self.do_POST_add_entry()
		elif path[0] == 'entries' and len(path) > 1:
			self.do_POST_modify_entry(path[1])
		else:
			return
#------------------------------------------------------------------------------------------------------
	'''
	Adds a new entry
	@args:
	@return: Status code
	'''
	def do_POST_add_entry(self):
		post_data = self.parse_POST_request()
		text = post_data["entry"][0] if "entry" in post_data else None
		if text != None and self.server.add_value_to_store(text):
			self.send_response(200)
		else:
			self.send_error(400, "Value was not added.")

#------------------------------------------------------------------------------------------------------
	'''
	Modifies a specific entry
	@args:
	@return: Status code
	'''
	def do_POST_modify_entry(self, entryID):
		post_data = self.parse_POST_request()
		delete = post_data["delete"] if "delete" in post_data else None
		if delete == None:
			status_code = 400
		elif delete[0] == '1':
			status_code = self.do_POST_delete_entry(int(entryID))
		else:
			entry = post_data["entry"] if "entry" in post_data else None
			status_code = 200 if self.server.modify_value_in_store(int(entryID), entry[0]) else 400
		self.send_response(status_code)

#------------------------------------------------------------------------------------------------------
	'''
	Deletes an entry
	@args: none
	@return: Status code
	'''
	def do_POST_delete_entry(self, entryID):
		status_code = 200 if entryID != None and self.server.delete_value_in_store(entryID) else 400
		return status_code
#------------------------------------------------------------------------------------------------------





#------------------------------------------------------------------------------------------------------
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
