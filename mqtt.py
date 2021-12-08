#! /usr/bin/python3

import socket
import logging
import sys
import os
import traceback
import select
from sys import byteorder, stdin
from typing import BinaryIO, Tuple

PORT = 1883
TYPE_CONNECT = 0x10
TYPE_CONNACK = 0x20
TYPE_PUBLISH = 0x30
TYPE_SUBREQ = 0x82
TYPE_SUBACK = 0x90

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
	client_ID = client_ID.encode("utf-8")
	client_ID_length = len(client_ID).to_bytes(2,byteorder="big")

	header = (TYPE_CONNECT).to_bytes(1, byteorder = "big")
	proto_name = "MQTT".encode("utf-8")
	proto_lenght = len(proto_name).to_bytes(2,byteorder="big")
	version = (4).to_bytes(1,byteorder="big")
	connect_flags = (0x02).to_bytes(1,byteorder="big")
	keepalive = (60).to_bytes(2,byteorder="big")
	message_length = (2 + 4 + 1 + 1 + 2 + int.from_bytes(client_ID_length,byteorder="big") + 2).to_bytes(1,byteorder="big") # size protocol name length + size protocol name + size version + size CONNECT flags + size keep alive + size client id length + size client ID
	return (header + message_length + proto_lenght + proto_name + version + connect_flags + keepalive + client_ID_length + client_ID) 

def create_mqtt_subscriber_msg(topic):
	return

def create_mqtt_suback_msg():
	return

def create_mqtt_connack_msg(accepted=True):
	header = (TYPE_CONNACK).to_bytes(1,byteorder="big")
	msglen = (2).to_bytes(1,byteorder="big")
	flags = (0).to_bytes(1,byteorder="big")
	if accepted:
		returncode = (0).to_bytes(1,byteorder="big")
	else:
		returncode = (1).to_bytes(1,byteorder="big")
	
	return header + msglen + flags + returncode

def decode_msg(msg):
	if msg[:1] == TYPE_CONNECT.to_bytes(1,byteorder="big"):
		typemsg = "CONNECT"
		keepalive = int.from_bytes(msg[11:12],byteorder="big")
		clientid = msg[14:].decode("utf-8")
		return (typemsg,keepalive,clientid)

	if msg[:1] == TYPE_CONNACK.to_bytes(1,byteorder='big'):
		typemsg = "CONNACK"
		ackflags = msg[2:3].decode('utf-8')
		code = int.from_bytes(msg[3:4],byteorder="big")
		return (typemsg,ackflags,code)


	if msg[:1] == TYPE_SUBREQ.to_bytes(1,byteorder="big"):
		typemsg = "SUBREQ"
		msgid = int.from_bytes(msg[2:3],byteorder="big")
		topiclenght = int.from_bytes(msg[3:4],byteorder="big")
		topic = msg[4:4+topiclenght].decode('utf-8')
		return (typemsg,msgid,topic)

	if msg[:1] == TYPE_SUBACK.to_bytes(1,byteorder="big"):
		typemsg = "SUBACK"
		msgid = int.from_bytes(msg[2:4],byteorder="big")
		return (typemsg,msgid)

	if msg[:1] == TYPE_PUBLISH.to_bytes(1,byteorder="big") or msg[:1] == (TYPE_PUBLISH+1).to_bytes(1,byteorder="big"):
		typemsg = "PUBLISH"
		topiclenght = int.from_bytes(msg[2:4],byteorder="big")
		topic = msg[4:4+topiclenght].decode('utf-8')
		message = msg[4+topiclenght:].decode('utf-8')
		if msg[:1] == TYPE_PUBLISH.to_bytes(1,byteorder="big"):
			return (typemsg,topic,message,False)
		return (typemsg,topic,message,True)
	return tuple("ERROR")

# print(create_mqtt_connect_msg("mosq-6F4yNCdkrVx80t8BVp"))
# print(decode_msg(create_mqtt_connect_msg("mosq-6F4yNCdkrVx80t8BVp")))
# print(create_mqtt_publish_msg("monsieur ", "théophyl"))
# print(decode_msg(create_mqtt_publish_msg("monsieur ", "théophyl")))

def run_publisher(addr, topic, pub_id, retain=False):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(addr)
	s.sendall(create_mqtt_connect_msg(pub_id))
	connack = s.recv(127)
	if decode_msg(connack)[0] == "CONNACK" and decode_msg(connack)[2] == 0:
		while True:
			msg = input()
			s.sendall(create_mqtt_publish_msg(topic,msg,retain))
	pass


def run_subscriber(addr, topic, sub_id):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(addr)
	s.sendall(create_mqtt_connect_msg(sub_id))
	connack = s.recv(127)
	if decode_msg(connack)[0] == "CONNACK" and decode_msg(connack)[2] == 0:
		s.sendall(create_mqtt_subscriber_msg(topic))
		suback = s.recv(127)
		if decode_msg(suback)[0] == 'SUBACK':
			while True:
				tmp = decode_msg(s.recv(127))
				if tmp[0] == "PUBLISH":
					print(tmp[1] + ' : ' + tmp[2])
	pass


def run_server(addr):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(addr)
	s.listen(1)
	l = [s]
	listconnected = []
	while True:
		l3, _, _ = select.select(l,[],[])
		for i in l3:
			if i == s:
				conn, _ = i.accept()
				l.append(conn)
			else:
				data = i.recv(1500)
				data = decode_msg(data)
				if data[0] == "CONNECT":
					i.sendall(create_mqtt_connack_msg(True))
					listconnected.append([i,None])
				elif data[0] == "SUBREQ":
					for o in listconnected:
						if i in o:
							o[1] = data[2]
					i.sendall(create_mqtt_suback_msg())
				elif data[0] == "PUBLISH":
					for o in listconnected:
						if data[1] in o:
							o[0].sendall(create_mqtt_publish_msg(data[1],data[2],data[3]))
	pass