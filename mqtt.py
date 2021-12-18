#! /usr/bin/python3

import socket
import logging
import sys
import os
import traceback
import select
from sys import byteorder, exc_info, stdin
from typing import BinaryIO, Tuple

PORT = 1883
TYPE_CONNECT = 0x10
TYPE_CONNACK = 0x20
TYPE_PUBLISH = 0x30
TYPE_SUBREQ = 0x82
TYPE_SUBACK = 0x90
TYPE_DISCONNECT = 0xe0


def create_mqtt_publish_msg(topic, value, retain=False):
	""" create mqtt publish msg
    >>> create_mqtt_publish_msg("temp","45")
    b'0\\x08\\x00\\x04temp45'
    """
	retain_code = 0
	if retain:
		retain_code = 1
	# on cherche la taille de topic et value
	topic.encode("ascii")
	topic_length = len(topic)
	value.encode("ascii")
	value_length = len(value)
	# total
	message_length = value_length + topic_length + 2
	request = (TYPE_PUBLISH + retain_code).to_bytes(1, byteorder="big") + (message_length).to_bytes(1, byteorder='big') + (topic_length).to_bytes(
	    2, byteorder='big') + topic.encode("ascii") + value.encode("ascii")
	return request


def create_mqtt_connect_msg(client_ID):
	client_ID = client_ID.encode("ascii")
	client_ID_length = len(client_ID).to_bytes(2, byteorder="big")

	header = (TYPE_CONNECT).to_bytes(1, byteorder="big")
	proto_name = "MQTT".encode("ascii")
	proto_lenght = len(proto_name).to_bytes(2, byteorder="big")
	version = (4).to_bytes(1, byteorder="big")
	connect_flags = (0x02).to_bytes(1, byteorder="big")
	keepalive = (60).to_bytes(2, byteorder="big")
	# size protocol name length + size protocol name + size version + size CONNECT flags + size keep alive + size client id length + size client ID
	message_length = (2 + 4 + 1 + 1 + 2 + int.from_bytes(client_ID_length, byteorder="big") + 2).to_bytes(1, byteorder="big")
	return (header + message_length + proto_lenght + proto_name + version + connect_flags + keepalive + client_ID_length + client_ID)


def create_mqtt_subscriber_msg(topic):
	topic = topic.encode("ascii")
	topic_length = len(topic).to_bytes(2, byteorder="big")
	message_identifier = (1).to_bytes(2, byteorder="big")
	header = (TYPE_SUBREQ).to_bytes(1, byteorder="big")
	requested_qos = (0).to_bytes(1, byteorder="big")
	message_length = (1 + 2 + 2 + 6 + 1).to_bytes(1, byteorder="big")
	return (header + message_length + message_identifier + topic_length + topic + requested_qos)


def create_mqtt_suback_msg():
	header = (TYPE_SUBACK).to_bytes(1, byteorder="big")
	message_identifier = (1).to_bytes(2, byteorder="big")
	requested_qos = (0).to_bytes(1, byteorder="big")
	message_length = (2 + 1).to_bytes(1, byteorder="big")
	return (header + message_length + message_identifier + requested_qos)


def create_mqtt_connack_msg(accepted=True):
	header = (TYPE_CONNACK).to_bytes(1, byteorder="big")
	msglen = (2).to_bytes(1, byteorder="big")
	flags = (0).to_bytes(1, byteorder="big")
	if accepted:
		returncode = (0).to_bytes(1, byteorder="big")
	else:
		returncode = (1).to_bytes(1, byteorder="big")

	return header + msglen + flags + returncode


def create_mqtt_disconnect_msg():
	header = (TYPE_DISCONNECT).to_bytes(1, byteorder="big")
	msglen = (0).to_bytes(1, byteorder='big')
	return header + msglen


def decode_msg(msg):
	finished = True
	if msg[:1] == TYPE_CONNECT.to_bytes(1, byteorder="big"):
		typemsg = "CONNECT"
		keepalive = int.from_bytes(msg[11:12], byteorder="big")
		clientid = msg[14:].decode("ascii")
		return [(typemsg, keepalive, clientid)]

	if msg[:1] == TYPE_CONNACK.to_bytes(1, byteorder='big'):
		typemsg = "CONNACK"
		ackflags = msg[2:3].decode('ascii')
		code = int.from_bytes(msg[3:4], byteorder="big")
		return [(typemsg, ackflags, code)]

	if msg[:1] == TYPE_SUBREQ.to_bytes(1, byteorder="big"):
		typemsg = "SUBREQ"
		msgid = int.from_bytes(msg[2:4], byteorder="big")
		topiclenght = int.from_bytes(msg[4:6], byteorder="big")
		topic = msg[6:6 + topiclenght].decode('ascii')
		return [(typemsg, msgid, topic)]

	if msg[:1] == TYPE_SUBACK.to_bytes(1, byteorder="big"):
		typemsg = "SUBACK"
		msg_lenght = int.from_bytes(msg[1:2], byteorder='big')
		msgid = int.from_bytes(msg[2:4], byteorder="big")
		if (len(msg[2 + msg_lenght:]) != 0):
			finished = False
		if not finished:
			return [(typemsg, msgid)] + decode_msg(msg[2 + msg_lenght:])
		return [(typemsg, msgid)]

	if msg[:1] == TYPE_DISCONNECT.to_bytes(1, byteorder="big"):
		typemsg = "DISCONNECT"
		msglen = msg[1:]
		return [(typemsg, msglen)]

	if msg[:1] == TYPE_PUBLISH.to_bytes(1, byteorder="big") or msg[:1] == (TYPE_PUBLISH + 1).to_bytes(1, byteorder="big"):
		typemsg = "PUBLISH"
		messagelenght = int.from_bytes(msg[1:2], byteorder="big")
		topiclenght = int.from_bytes(msg[2:4], byteorder="big")
		topic = msg[4:4 + topiclenght].decode('ascii')
		message = msg[4 + topiclenght:2 + messagelenght].decode('ascii')
		if (len(msg[2 + messagelenght:]) != 0):
			finished = False
		if msg[:1] == TYPE_PUBLISH.to_bytes(1, byteorder="big"):
			if not finished:
				return [(typemsg, topic, message, False)] + decode_msg(msg[2 + messagelenght:])
			return [(typemsg, topic, message, False)]
		if not finished:
			return [(typemsg, topic, message, True)] + decode_msg(msg[2 + messagelenght:])
		return [(typemsg, topic, message, True)]
	return [tuple("ERROR")]


# print(create_mqtt_connect_msg("mosq-6F4yNCdkrVx80t8BVp"))
# print(decode_msg(create_mqtt_connect_msg("mosq-6F4yNCdkrVx80t8BVp")))
# print(create_mqtt_publish_msg("monsieur ", "théophyl"))
# print(decode_msg(create_mqtt_publish_msg("monsieur ", "théophyl")))


def run_publisher(addr, topic, pub_id, retain=False):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(addr)
		s.sendall(create_mqtt_connect_msg(pub_id))
		connack = s.recv(127)
		if decode_msg(connack)[0][0] == "CONNACK" and decode_msg(connack)[0][2] == 0:
			for line in stdin:
				s.sendall(create_mqtt_publish_msg(topic, line[:-1], retain))
		s.sendall(create_mqtt_disconnect_msg())
	except KeyboardInterrupt:
		s.sendall(create_mqtt_disconnect_msg())


def run_subscriber(addr, topic, sub_id):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(addr)
		s.sendall(create_mqtt_connect_msg(sub_id))
		connack = s.recv(127)
		data = decode_msg(connack)
		if data[0][0] == "CONNACK" and data[0][2] == 0:
			s.sendall(create_mqtt_subscriber_msg(topic))
			suback = s.recv(127)
			data = decode_msg(suback)
			if data[0][0] == 'SUBACK':
				if len(data) > 1:
					for d in data:
						if d[0] == "PUBLISH":
							print(d[1] + ' : ' + d[2])
				while True:
					pkt = s.recv(1500)
					tmp = decode_msg(pkt)
					for d in tmp:
						if d[0] == "PUBLISH":
							print(d[1] + ' : ' + d[2])
		pass
	except KeyboardInterrupt:
		s.sendall(create_mqtt_disconnect_msg())


def run_server(addr):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(addr)
	s.listen(1)
	l = [s]
	listconnected = []
	retainmsg = []
	while True:
		l3, _, _ = select.select(l, [], [])
		for i in l3:
			if i == s:
				conn, _ = i.accept()
				l.append(conn)
			else:
				data = i.recv(1500)
				data = decode_msg(data)
				for i_data in data:
					if i_data[0] == "CONNECT":
						i.sendall(create_mqtt_connack_msg(True))
						listconnected.append([i, None])
					elif i_data[0] == "SUBREQ":
						for o in listconnected:
							if i in o:
								o[1] = i_data[2]
								i.sendall(create_mqtt_suback_msg())
								for i_retainmsg in retainmsg:
									if i_retainmsg[0] == i_data[2]:
										i.sendall(create_mqtt_publish_msg(i_data[2], i_retainmsg[1]))
										break
					elif i_data[0] == "DISCONNECT":
						i.close()
						l.remove(i)
						for o in listconnected:
							if i in o:
								listconnected.remove(o)
					elif i_data[0] == "PUBLISH":
						if i_data[3]:
							topic_already_on_retain = False
							for i_retainmsg in range(len(retainmsg)):
								if i_data[1] == retainmsg[i_retainmsg][0]:
									topic_already_on_retain = True
									retainmsg[i_retainmsg][1] = i_data[2]
									break
							if not topic_already_on_retain:
								retainmsg.append([i_data[1], i_data[2]])
						for o in listconnected:
							if i_data[1] in o:
								pkt = create_mqtt_publish_msg(i_data[1], i_data[2], i_data[3])
								o[0].sendall(pkt)
	pass
