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

def getInformation(whole_data):
    try:
        method = whole_data[0].split(" ")
        host = whole_data[1].split(" ")

    #return ''.join(format(ord(i), '08b') for i in method[0]), ''.join(format(ord(i), '08b') for i in host[1])
    #print(method)
    #print(host)
        return method[0],host[1]
    except:
        return "EXIT", "EXIT"

def methodProcessing(message):
    valid_methods = ("GET","POST","HEAD")
    try:
        method = message.split()[0]
        print(method)
        url = message.split()[1]
        print(url)
        domain = url.split()[4]
        print(domain)
        #method = request.split()[0]
        if method not in valid_methods:
            return #403
        #send_msg = request.split()[0] + " / " + request.split()[2] + "\r\nHost:" + domain_msg.split()[1] + "\r\n\r\n"
        #print(request,domain_msg,domain,method,send_msg)
    except:
        print("No data received")
        return

    page = socket(AF_INET,SOCK_STREAM)
    data = b""
    buffer_size = 4096
    process_time = 5
    page.settimeout(process_time)
    page.connect((domain, 80))
    page.sendall(message.encode("ISO-8859-1"))
    try:
        while 1:
            chunk = page.recv(buffer_size)
            if len(chunk) == 0:
                print("No content left")
                break
            data += chunk
        #data = page.recv(buffer_size)
    except:
        print("Waited too long")

    #print(method)
    page.close()
    true_data = data.decode()
    print("Data received: ")
    whole = true_data.split("\r\n")
    # debugPrinting(whole)
    for i in whole:
        print(i)
    #return whole

def connect(client, address):
    #Receiving data
    data = b""
    buffer_size = 4096
    process_time = 5
    """conn.settimeout(process_time)
    try:
        while 1:
            chunk = conn.recv(buffer_size)
            if len(chunk) == 0:
                print("No content left")
                break
            data += chunk
    except:
        print("Waited too long")"""
    msg = client.recv(buffer_size)
    msg = msg[:-2]+b"Connection: Close\r\n\r\n"
    message = msg.decode("ISO-8859-1")

    #whole = message.split("\r\n")
    #debugPrinting(whole)
    #for i in whole:
    #    print (i)
    methodProcessing(message)
    client.close()


#Set up the server
proxy = socket(AF_INET,SOCK_STREAM)
#s.connect((hostName,80))
proxy.bind(("127.0.0.1",8888))
proxy.listen(10)
data_1 = []
data_2 = []
while True:
    print("Waiting...")
    clientSock, address = proxy.accept()
    print("Connected to ", address)
    connect(clientSock,address)
print("End")
s.close()
