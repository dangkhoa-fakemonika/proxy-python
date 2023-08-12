#external libraries
import socket
from socket import *
import sys
import threading
import time as pytime
from datetime import datetime, time
import os
import re

def debugPrinting(whole_data):
    try:
        db_file = open("ex.txt","x")
    except:
        db_file = open("ex.txt","a")
    for i in whole_data:
        db_file.write(i)
        db_file.write("\n")

    db_file.write("\nend of debugging one\n\n\n")
    db_file.close()

def getData(hostName, method):
    #Set up the server
    s = socket(AF_INET,SOCK_STREAM)
    s.connect((hostName,80))
    method_str = b""
    if (method == 0):
        method_str = b"GET"
    elif (method == 1):
        method_str = b"HEAD"
    elif (method == 2):
        method_str = b"POST"

    if (method_str == b""):
        print("NOT SUPPORTED METHOD")
        return

    req_sequence = method_str + b" / HTTP/1.1\r\nHost:www.example.com\r\n\r\n"

    #Sent request
    sent_bytes = 0 #Counting bytes
    while sent_bytes < len(req_sequence):
        sent_bytes += s.send(req_sequence[sent_bytes:])

    #Receiving data

    data = b""
    buffer_size = 4096
    process_time = 3
    s.settimeout(process_time)
    try:
        while 1:
            chunk = s.recv(buffer_size)
            if len(chunk) == 0:
                print("No content left")
                break
            data += chunk
    except:
        print("Waited too long")
    #data = s.recv(buffer_size)
    true_data = data.decode("ISO-8859-1")

    whole = true_data.split("\r\n")
    debugPrinting(whole)
    for i in whole:
        print (i)
    s.close()

getData("example.com",0)