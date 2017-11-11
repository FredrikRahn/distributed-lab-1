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
import urllib2 #Used for opening files
from urlparse import parse_qs # Parse POST data
from httplib import HTTPConnection # Create a HTTP connection, as a client (for POST requests to the other vessels)
from urllib import urlencode # Encode POST content into the HTTP header
from codecs import open # Open a file
from threading import  Thread # Thread Management
#------------------------------------------------------------------------------------------------------

# Global variables for HTML templates
board_frontpage_header_template = open('board_frontpage_header_template.html', 'r').read()
boardcontents_template = open('boardcontents_template.html', 'r').read()
entry_template = open('entry_template.html', 'r').read()
board_frontpage_footer_template = open('board_frontpage_footer_template.html', 'r').read()
index = board_frontpage_header_template + boardcontents_template + entry_template + board_frontpage_footer_template

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
		self.store[++self.current_key]=value
		pass
#------------------------------------------------------------------------------------------------------
	# We modify a value received in the store
	def modify_value_in_store(self,key,value):
		if self.store[key]:					#If Key exists
			self.store[key] = value			#update key value to value
		else:
			return							#if key doesnt exist, return
		pass
#------------------------------------------------------------------------------------------------------
	# We delete a value received from the store
	def delete_value_in_store(self,key):
		if self.store[key]:					#if key exists
			del self.store[key]				#delete entry
		else:
			return							#if key doesnt exist, return
		pass
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
			connection = HTTPConnection("%s:%d" % (vessel, PORT_NUMBER), timeout = 30)
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
			print "Error while contacting %s" % vessel
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
		self.do_GET_Index()
#------------------------------------------------------------------------------------------------------
# GET logic - specific path
#Implement /board
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
		fetch_index_contents = boardcontents_template
		fetch_index_entries = entry_template
		fetch_index_footer = board_frontpage_footer_template

		# We should do some real HTML here
		html_response = fetch_index_header + fetch_index_contents + fetch_index_entries + fetch_index_footer
		#In practice, go over the entries list,
		#produce the boardcontents part,
		#then construct the full page by combining all the parts ...

		self.wfile.write(html_response)
#------------------------------------------------------------------------------------------------------
	'''
	Lists all available entries
	@args:
	@return: List of entries
	'''
	def do_GET_all_entries(self):
		# We set the response status code to 200 (OK)
		self.set_HTTP_headers(200)
		#Add temp entry to store to check if it works
		self.server.store['ENTRY-OF-DESTINY-ID']="The entry of destinys ninth dragon of the eleventh sin"
		return self.server.store.items()
#------------------------------------------------------------------------------------------------------
	'''
	Retrieve entry
	@args:
	@return: Entry:html
	'''
	def do_GET_entry(self):							#Fetch specific entry
		self.set_HTTP_headers(200)
		html_reponse = "TEMPORARY SHIET"
		self.wfile.write(html_response)
#------------------------------------------------------------------------------------------------------
# Request handling - POST
#------------------------------------------------------------------------------------------------------
	def do_POST(self):
		print("Receiving a POST on %s" % self.path)
		# Here, we should check which path was requested and call the right logic based on it
		# We should also parse the data received
		# and set the headers for the client

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
#------------------------------------------------------------------------------------------------------
	'''
	Adds a new entry
	@args: entry:text
	@return: Status code
	'''
	def do_POST_modify_entry(self):
		self.set_HTTP_headers(200)
		html_reponse = "TEMPORARY SHIET"
		self.wfile.write(html_response)
#------------------------------------------------------------------------------------------------------
	'''
	Modifies a specific entry
	@args: entry:text
	@return: Status code
	'''
	def do_POST_modify_entry(self):
		self.set_HTTP_headers(200)
		html_reponse = "TEMPORARY SHIET"
		self.wfile.write(html_response)
#------------------------------------------------------------------------------------------------------
	'''
	Deletes an entry
	@args: none
	@return: Status code
	'''
	def do_POST_delete_entry(self):
		self.set_HTTP_headers(200)
		html_reponse = "TEMPORARY SHIET"
		self.wfile.write(html_response)
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
