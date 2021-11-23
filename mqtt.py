#! /usr/bin/python3

import socket
import logging
import sys
import os
import traceback
import select
from sys import stdin

PORT = 1883

def create_mqtt_publish_msg(topic, value, retain=False):
    """
    Creates a MQTT packet of type PUBLISH with DUP Flag=0 and QoS=0.
    """
    pass


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
    """
    Run main server loop
    """
    pass