#external libraries
import socket
from socket import *
import sys
import threading
import time as pytime
from datetime import date, datetime, time
import os
import re
import json

buffer_size = 4096
process_time = 5

##################################### CONFIG FILE READING #######################################
def readJSONConfigFile(filename):
    config_file = open(filename,"r")
    read_data = json.load(config_file)

    content = ("cache_time","whitelisting_enabled","whitelist","time_restriction","time_allow","decode_format")
    cache_time = int(read_data["cache_time"])
    WLenabled = bool(read_data["whitelisting_enabled"])
    whitelist = read_data["whitelist"]
    restriction = read_data["time_restriction"]
    time_allow = read_data["time_allow"]
    supported_img = read_data["supported_img_types"]

    return cache_time,WLenabled,whitelist,restriction,time_allow,supported_img

#Read config file
cache_time,WLenabled,whitelist,restriction,time_allow,supported_img = readJSONConfigFile("config.json")

######################################## REQUEST HANDLING ##########################################

def getRequest(message,method,domain, url):
    if method == "GET":
        return method + " " + url + " HTTP/1.1\r\nHost:" + domain + "\r\nConnection: close\r\n\r\n"
    if method == "HEAD":
        return method + " " + url + " HTTP/1.1\r\nHost:" + domain + "\r\nAccept: text/html\r\nConnection: close\r\n\r\n"
    if method == "POST":
        request = method + " " + url + " HTTP/1.1\r\n"
        if message.find("Connection") == -1:
            request += message.partition("\r\n\r\n")[0] + "\r\nConnection: close\r\n\r\n" + message.partition("\r\n\r\n")[2]
        else:
            request += message.partition("\r\n")[2].partition("Connection: ")[0] + "Connection: close\r\n" + message.partition("Connection: ")[2].partition("\r\n")[2]
        return request

def return403(client_connect):
    error_file = open("error403.html",'r')
    error_text = error_file.read()
    client_connect.send(b'HTTP/1.0 403 Forbidden\r\nContent-Type: text/html\r\n\r\n' + error_text.encode("ISO-8859-1"))

    print("#################################")
    print("Process Terminated")
    print("#################################")

######################################### DATA PROCESSING #########################################################
def writeReceiveData(message,method,domain,url):
    request = getRequest(message,method, domain, url)
    page = socket(AF_INET, SOCK_STREAM)
    data = b""
    page.settimeout(process_time)
    page.connect((domain, 80))

    page.sendall(request.encode("ISO-8859-1"))
    #Searching for Transfer-Encoding/Content-Length in header
    while 1:
        tmpbit = page.recv(1)
        data += tmpbit
        if b"\r\n\r\n" in data:
            break
    print("Decode process: ")
    print(data.decode("ISO-8859-1"))
    print("End of decode")
    if b"Transfer-Encoding: chunked" in data and 1:
        while 1:
            try:
                #Read the number
                number = b""
                while 1:
                    tmpbit = page.recv(1)
                    number += tmpbit
                    if b"\r\n" in number:
                        break
                data += number
                num = int(number.strip(b'\r\n'),16)

                if num == 0:
                    break
                else:
                    try:
                        while 1:
                            chunk = page.recv(min(buffer_size, num))
                            if len(chunk) == 0:
                                print("No content left")
                                break
                            data += chunk
                            num -= len(chunk)
                            if num <= 0:
                                break
                    except:
                        print("End of line data")
            except:
                print("Waited too long")
    elif b"Content-Length: " in data and 1:
        num = int(data.decode("ISO-8859-1").partition("Content-Length: ")[2].partition("\r\n")[0])
        print("Length:",num)
        try:
            while 1:
                chunk = page.recv(min(buffer_size,num))
                if len(chunk) == 0:
                    print("No content left")
                    break
                data += chunk
                num -= len(chunk)
                if num <= 0:
                    break
        except:
            print("End of line data")
    else:
        #Main process
        try:
            while 1:
                chunk = page.recv(buffer_size)
                if len(chunk) == 0:
                    print("No content left")
                    break
                data += chunk
        except:
            print("Waited too long")

    page.close()
    return data
##################################################DATA HANDLING###############################################
def saveCacheImages(response,domain,path,file_name):
    cache_img_content = response.partition("\r\n\r\n")[2].encode("ISO-8859-1")
    cache_img = open("cache/" + domain + "/" + path + "/" + file_name, "wb")
    cache_img.write(cache_img_content)
    cache_img.close()
    cache_header_content = response.partition("\r\n\r\n")[0].encode("ISO-8859-1")
    cache_img_header = open("cache/" + domain + "/" + path + "/" + file_name.partition(".")[0] + ".bin", "wb")
    cache_img_header.write(cache_header_content)
    cache_img_header.write(b"\r\n\r\n" + datetime.now().strftime("%H/%M/%S/%d/%m/%y").encode("ISO-8859-1"))
    cache_img_header.close()

def createCacheData(message,method,domain,url):
    if 0 or method != 'GET' or message.partition("\r\n\r\n")[0].find("Accept: image") == -1: #I dont like caching for other methods
        data = writeReceiveData(message,method,domain,url)
        response = data.decode("ISO-8859-1")
        print(response)
    else:
        file_name = url.split("/").pop()
        extension = file_name.partition(".")[2]
        path = url.partition("http://" + domain)[2].partition("/" + file_name)[0]

        if extension not in supported_img:
            data = writeReceiveData(message, method, domain, url)
            response = data.decode("ISO-8859-1")
            print(response)
            return

        try:
            # No folder for caching (no data cached)
            os.makedirs("cache/" + domain + "/" + path)
            data = writeReceiveData(message,method,domain,url)
            response = data.decode("ISO-8859-1")
            saveCacheImages(response,domain,path,file_name)
        except:
            try:
                #Check for cached file existing
                cache_img = open("cache/" + domain + "/" + path + "/" + file_name, "rb")
                cache_img.close()
                cache_img_header = open("cache/" + domain + "/" + path + "/" + file_name.partition(".")[0] + ".bin", "rb")
                cache_img_header.close()
                cache_header = cache_img_header.read().decode("ISO-8859-1")
                header,blank,timecheck = cache_header.partition("\r\n\r\n")
                dd,mm,yy,hh,mm,ss = timecheck.split("/")
                getdate = datetime(yy,mm,dd,hh,mm,ss) + datetime.timedelta(seconds=cache_time)
                if getdate > datetime.now():
                    raise TypeError() #Cancel cache to write new cache

                response = header + "\r\n\r\n"+ cache_img.read().decode("ISO-8859-1")
                data = response.encode("ISO-8859-1")

            except:
                data = writeReceiveData(message,method,domain,url)
                response = data.decode("ISO-8859-1")
                saveCacheImages(response,domain,path,file_name)
    return data

########################################### METHOD PROCESSSING ########################################################

def methodProcessing(message,client):
    try:
        method = message.split()[0]
        url = message.split()[1]
        domain = message.split()[4]
        print("URL:",url)
    except:
        print("No data received")
        return

    #Kiểm tra phương thức hợp lệ
    if method not in ("GET","POST","HEAD"):
            return403(client)
            return #403

    #Danh sách cho phép
    if WLenabled:
        if domain not in whitelist:
            print("Not available")
            return403(client)
            return #403

    ##################### GO TO WRITE RECEIVE DATA IF GONE WRONG ########################
    data = createCacheData(message,method,domain,url)
    #####################################################################################

    response = data.decode("ISO-8859-1")
    client.send(data)
    print("Data received: ")
    whole = response.split("\r\n")
    for i in whole:
        if 1 or i.isspace():
            break
        print(i)

def connectionProcessing(client, address):
    if restriction:
        if (time(time_allow[0],0,0) < datetime.now().time() < time(time_allow[1],0,0)):
            print("Not available")
            return403(client)
            return #403

    #Receiving data
    data = b""
    msg = client.recv(buffer_size)
    #msg = msg[:-2]+b"Connection: Close\r\n\r\n"
    message = msg.decode("ISO-8859-1")

    whole = message.split("\r\n")
    for i in whole:
        print(i)
    methodProcessing(message,client)
    client.close()

    print("########################################")
    print("Connection to",addr_name,"ended! ")
    print("########################################")


############################################## PROXY MAIN #################################################################

proxy = socket(AF_INET,SOCK_STREAM)
proxy.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
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

