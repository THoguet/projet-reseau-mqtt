#! /usr/bin/python3

import socket
import logging
import sys
import os
import traceback
import select
from sys import stdin

PORT = 1883
TYPE_CONNECT = 0x10
TYPE_PUBLISH = 0x30

def create_mqtt_publish_msg(topic, value, retain=False):
    """ create mqtt publish msg
    >>> create_mqtt_publish_msg("temp","45")
    b'0\\x08\\x00\\x04temp45'
    """
    retain_code = 0
    if retain:
        retain_code = 1
    #on cherche la taille de topic et value
    topic.encode("utf-8")
    topic_length = len(topic)
    value.encode("utf-8")
    value_length = len(value)
    #total
    message_length = value_length + topic_length + 2
    request = (TYPE_PUBLISH + retain_code).to_bytes(1, byteorder="big") + (message_length).to_bytes(1, byteorder = 'big') + (topic_length).to_bytes(2, byteorder = 'big') + topic.encode("utf-8") + value.encode("utf-8")
    return request

def create_mqtt_connect_msg(client_ID): 
    client_ID.encode("utf-8")
    client_ID_length = len(client_ID)

    header = (TYPE_CONNECT).to_bytes(1, byteorder = "big")
    message_length = 2 + 4 + 1 + 1 + 2 + client_ID_length + 2 # size protocol name length + size protocol name + size version + size CONNECT flags + size keep alive + size client id length + size client ID

    

print(create_mqtt_publish_msg("monsieur ", "théophyl").decode("utf-8"))

def run_publisher(addr, topic, pub_id, retain=False):
	"""
	Run client publisher.
	"""
	pass


def run_subscriber(addr, topic, sub_id):
	"""
	Run client subscriber.
	"""
	pass


def run_server(addr):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(addr)
	s.listen(1)
	l = [s]
	while True:
		l3, _, _ = select.select(l,[],[])
		for i in l3:
			if i == s:
				conn, _ = i.accept()
				l.append(conn)
			else:
				data = i.recv(1500)
				if not data:
					i.close()
					l.remove(i)
				else:	
					print(data.decode('utf-8'))
					i.sendall(data)
	pass

#!/usr/bin/python3
# import socket
# import sys
# try:
# 	host = sys.argv[1]
# except:
# 	print("Erreur pas d'arguements :/")
# 	sys.exit(1)
# try:
# 	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# except Exception as e :
# 	print("Erreur de socket :/\n"+str(e))
# 	sys.exit(1)
# port = 80
# try:
# 	s.connect((host, port))
# except socket.gaierror as e: 
# 	print ("Adresse incorrecte: "+str(e)) 
# 	sys.exit(1)
# except socket.timeout as e: 
# 	print ("Connection timeout: "+str(e)) 
# 	sys.exit(1)
# except Exception as e: 
# 	print ("Erreur de connection: "+str(e)) 
# 	sys.exit(1) 
# request = "GET / HTTP/1.1\r\n" \
# "Host: " + host + "\r\n" \
# "Connection: close\r\n\r\n"
# s.send(request.encode("utf-8"))
# data = "bjr"
# while data != b"":
# 	try:
# 		data = s.recv(4096)
# 	except Exception as e: 
# 		print ("Erreur lors de la reception des données: "+str(e)) 
# 		sys.exit(1) 
# 	print(data.decode("utf-8"),end="")
# s.close()