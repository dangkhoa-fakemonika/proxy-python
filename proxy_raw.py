#external libraries
import socket
from socket import *
import sys
import threading
import time as pytime
from datetime import datetime, time
import os
import re
import json

buffer_size = 4096
process_time = 5

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
def readJSONConfigFile(filename):
    config_file = open(filename,"r")
    read_data = json.load(config_file)

    content = ("cache_time","whitelisting_enabled","whitelist","time_restriction","time_allow","decode_format")
    cache_time = int(read_data["cache_time"])
    WLenabled = bool(read_data["whitelisting_enabled"])
    whitelist = read_data["whitelist"]
    restriction = read_data["time_restriction"]
    time_allow = read_data["time_allow"]

    return cache_time,WLenabled,whitelist,restriction,time_allow

cache_time,WLenabled,whitelist,restriction,time_allow = readJSONConfigFile("config.json")
def getRequest(method, domain):
    if method == "GET":
        return method + " / HTTP/1.0\r\nHost:" + domain + "\r\n\r\n"
    if method == "POST":
        return method + " /auth HTTP/1.0\r\n"
    if method == "HEAD":
        return method + " / HTTP/1.0\r\nHost:" + domain + "\r\nAccept: text/html\r\n"

def return403(client_connect):
    error_file = open("error403.html",'r')
    error_text = error_file.read()
    client_connect.send(b'HTTP/1.0 403 Forbidden\r\nContent-Type: text/html\r\n\r\n' + error_text.encode("ISO-8859-1"))

    print("#################################")
    print("Process Terminated")
    print("#################################")


def createCacheData(method,domain):
    try:
        os.makedirs("cache/"+ domain)
        ###################################### IF CODE GONE WRONG GO HERE ####################
        request = getRequest(method, domain)
        page = socket(AF_INET, SOCK_STREAM)
        data = b""
        page.settimeout(process_time)
        page.connect((domain, 80))

        page.sendall(request.encode("ISO-8859-1"))
        try:
            while 1:
                chunk = page.recv(buffer_size)
                if len(chunk) == 0:
                    print("No content left")
                    break
                data += chunk
        except:
            print("Waited too long")
        response = data.decode("ISO-8859-1")
        #print(response)
        # print(method)
        page.close()
        #######################################################################################
        cache_content = response.partition("\r\n\r\n")[2]
        cache_file = open("cache/" + domain + "/" + domain + ".html", "w")
        cache_file.write(cache_content)
        cache_file.close()
    except:
        try:
            cache_file = open("cache/" + domain + "/" + domain + ".html", "r")
            response = cache_file.read()
            data = response.encode("ISO-8859-1")
            cache_file.close()
        except:
            ###################################### IF CODE GONE WRONG GO HERE ####################
            request = getRequest(method, domain)
            page = socket(AF_INET, SOCK_STREAM)
            data = b""
            page.settimeout(process_time)
            page.connect((domain, 80))

            page.sendall(request.encode("ISO-8859-1"))
            try:
                while 1:
                    chunk = page.recv(buffer_size)
                    if len(chunk) == 0:
                        print("No content left")
                        break
                    data += chunk
            except:
                print("Waited too long")
            response = data.decode("ISO-8859-1")
            print(response)
            # print(method)
            page.close()
            #######################################################################################
            cache_content = response.partition("\r\n\r\n")[2]
            cache_file = open("cache/" + domain + "/" + domain + ".html", "w")
            cache_file.write(cache_content)
            cache_file.close()
    return data

def methodProcessing(message,client):
    try:
        method = message.split()[0]
        url = message.split()[1]
        domain = message.split()[4]
        #print(domain)
        url = url[url.find('://')+3:]
        file_path = url[url.find('/'):] 
        #send_msg = request.split()[0] + " / " + request.split()[2] + "\r\nHost:" + domain_msg.split()[1] + "\r\n\r\n"
        #print(request,domain_msg,domain,method,send_msg)
    except:
        print("No data received")
        return
    #Check valid method
    if method not in ("GET","POST","HEAD"):
            return #403
    #whitelist

    if WLenabled:
        if domain not in whitelist:
            print("Not available")
            return #403

    ##################### GO TO CREATE CACHE DATA IF GONE WRONG ########################
    data = createCacheData(method,domain)
    ####################################################################################
    response = data.decode("ISO-8859-1")
    client.send(data)
    print("Data received: ")
    #print(method)
    #print(response)
    whole = response.split("\r\n")
    #debugPrinting(whole)
    for i in whole:
        print(i)

def connectionProcessing(client, address):
    if restriction:
        if (datetime.now().time() < time(time_allow[0],0,0) or datetime.now().time() > time(time_allow[1],0,0)):
            print("Not available")
            return #403

    #Receiving data
    data = b""
    msg = client.recv(buffer_size)
    msg = msg[:-2]+b"Connection: Close\r\n\r\n"
    message = msg.decode("ISO-8859-1")

    #whole = message.split("\r\n")
    #debugPrinting(whole)
    #for i in whole:
    #    print (i)
    methodProcessing(message,client)
    client.close()

    print("########################################")
    print("Connection to",addr_name,"ended! ")
    print("########################################")


#Set up the server

proxy = socket(AF_INET,SOCK_STREAM)
proxy.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
#s.connect((hostName,80))
proxy.bind(("127.0.0.1",8888))
proxy.listen(10)
print("Currently listening...")

while True:
    clientSock, address = proxy.accept()
    addr_name = str(address[0]) + ' : ' + str(address[1]) # 127.0.0.1 : XXXXX

    print("#################################")
    print("Connected to", addr_name)
    print("#################################")

    #Initiate threading
    main_thread = threading.Thread(name=addr_name,target=connectionProcessing,args=(clientSock,addr_name))
    main_thread.start()

    #main_thread.join()
    #connectionProcessing(clientSock,address)
print("End")
proxy.close()
