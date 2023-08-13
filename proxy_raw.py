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

def useMethod():
    print()
def getData(conn, address):
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
    data = conn.recv(buffer_size)
    true_data = data.decode("ISO-8859-1")

    whole = true_data.split("\r\n")
    #debugPrinting(whole)
    for i in whole:
        print (i)

    """method_str, host_name = getInformation(whole)
    req_sequence = method_str + " / HTTP/1.1\r\nHost:www." + host_name + "\r\n\r\n"
    #print(req_sequence)
    if (method_str == "EXIT"):
        return
    request = req_sequence.encode("ISO-8859-1")
    # Sent request
    sent_bytes = 0  # Counting bytes

    data = b""
    while sent_bytes < len(request):
        sent_bytes += conn.send(request[sent_bytes:])
    try:
        while 1:
            chunk = conn.recv(buffer_size)
            if len(chunk) == 0:
                print("No content left")
                break
            data += chunk
    except:
        print("Waited too long")
    #data = s.recv(buffer_size)
    true_data = data.decode("ISO-8859-1")

    whole = true_data.split("\r\n")
    #debugPrinting(whole)
    for i in whole:
        print (i)"""
    conn.close()


#Set up the server
s = socket(AF_INET,SOCK_STREAM)
#s.connect((hostName,80))
s.bind(("127.0.0.1",8888))
s.listen(5)


while True:
    print("Waiting...")
    conn, address = s.accept()
    print("Connected to ", address)
    getData(conn,address)
    num = int(input("0 to continue "))
    if num:
        break
print("End")
s.close()
