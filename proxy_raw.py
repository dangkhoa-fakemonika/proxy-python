#external libraries
import socket
from socket import *
import threading
from datetime import date, datetime, timedelta, time
import os
import json

##################################### CONFIG FILE READING #######################################
def readJSONConfigFile(filename):
    #Open file
    config_file = open(filename,"r")
    read_data = json.load(config_file)

    #Proxy main configurations
    cache_time = int(read_data["cache_time"])
    buffer_size = int(read_data["buffer_size"])
    process_time = int(read_data["process_time"])

    #Whitelist configurations
    WLenabled = bool(read_data["whitelisting_enabled"])
    whitelist = read_data["whitelist"]

    #Time restriction configurations
    restriction = bool(read_data["time_restriction"])
    time_allow = read_data["time_allow"]

    #Decode
    decoder = read_data["decoder"]

    #Caching images configurations
    supported_img = read_data["supported_img"]

    return cache_time,WLenabled,whitelist,restriction,time_allow,supported_img,decoder,buffer_size,process_time

#Read config file
cache_time,WLenabled,whitelist,restriction,time_allow,supported_img,decoder,buffer_size,process_time = readJSONConfigFile("config.json")

######################################## REQUEST HANDLING ##########################################

def getRequest(message,method,domain,url):
    #Ensuring the right domain
    input_url = url
    if input_url.partition(domain)[2] == "/":
        url = input_url.partition(domain)[0] + input_url.partition(domain)[1]
    if input_url.partition("http://")[2].partition("/")[0] != domain:
        domain = input_url.partition("http://")[2].partition("/")[0]

    #Formatting requests
    if method == "GET":
        return method + " " + url + " HTTP/1.1\r\nHost:" + domain + "\r\nConnection: close\r\n\r\n"
    if method == "HEAD":
        #return method + " " + url + " HTTP/1.1\r\nHost:" + domain + "\r\nAccept: text/html\r\nConnection: close\r\n\r\n"
        return method + " " + url + " HTTP/1.1\r\nHost:" + domain + "\r\nConnection: close\r\n\r\n"
    if method == "POST":
        request = method + " " + url + " HTTP/1.1\r\n"
        if message.find("Connection") == -1:
            request += message.partition("\r\n\r\n")[0] + "\r\nConnection: close\r\n\r\n" + message.partition("\r\n\r\n")[2]
        else:
            request += message.partition("\r\n")[2].partition("Connection: ")[0] + "Connection: close\r\n" + message.partition("Connection: ")[2].partition("\r\n")[2]
        return request

def return403(client):

    with open("error/error403.html", "r") as error_file:
        error_text = error_file.read()
    print("error")

    client.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n' + error_text.encode() + b'\r\n')
    #client.sendall(error_text.encode())
    client.close()

    print("#################################")
    print("Process Terminated")
    print("#################################")

######################################### DATA PROCESSING #########################################################
def receiveResponseData(message,method,domain,url):
    #Get request format
    request = getRequest(message,method, domain, url)
    data = b""
    if url.partition("http://")[2].partition("/")[0] != domain:
        domain = url.partition("http://")[2].partition("/")[0]

    #Create server
    page = socket(AF_INET, SOCK_STREAM)
    page.settimeout(process_time) #Time out in case of reading
    page.connect((domain, 80))

    #Send the request
    page.sendall(request.encode(decoder))

    #Searching for Transfer-Encoding/Content-Length in header
    while 1:
        tmpbit = page.recv(1)
        data += tmpbit
        if b"\r\n\r\n" in data:
            break

    #Check for Transfer-Encoding
    if b"Transfer-Encoding: chunked" in data:
        while 1:
            try:
                #Read the number of each block
                number = b""
                while 1:
                    tmpbit = page.recv(1)
                    number += tmpbit
                    if b"\r\n" in number:
                        break
                data += number
                num = int(number.strip(b'\r\n'),16)

                #Read data block
                if num == 0: #End of data
                    data += b"\r\n"
                    break
                else:
                    num += 2
                    try:
                        while 1: #Use chunking method to guarantee data receiving
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
    #Check for Content-Length
    elif b"Content-Length: " in data:
        #Read the length
        num = int(data.decode(decoder).partition("Content-Length: ")[2].partition("\r\n")[0])
        print("Length:",num)
        try:
            while 1: #Use chunking method to guarantee data receiving
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
        #Subtitute process for rare cases
        try:
            while 1:
                chunk = page.recv(buffer_size)
                if len(chunk) == 0:
                    print("No content left")
                    break
                data += chunk
        except:
            print("Waited too long")

    #End communication from the web server
    page.close()
    return data
##################################################DATA HANDLING###############################################
def saveCacheImages(response,domain,path,file_name):

    #Save cache content
    cache_img_content = response.partition("\r\n\r\n")[2].encode(decoder)
    cache_img = open("cache/" + domain + "/" + path + "/" + file_name, "wb")
    cache_img.write(cache_img_content)
    cache_img.close()

    #Save cache header
    cache_header_content = response.partition("\r\n\r\n")[0].encode(decoder)
    cache_img_header = open("cache/" + domain + "/" + path + "/" + file_name.partition(".")[0] + ".bin", "wb")
    cache_img_header.write(cache_header_content)
    cache_img_header.write(b"\r\n\r\n" + datetime.now().strftime("%H/%M/%S/%d/%m/%y").encode(decoder))
    cache_img_header.close()

def createCacheData(message,method,domain,url):
    # Check for cache-able contents
    if method != 'GET' or message.partition("\r\n\r\n")[0].find("Accept: image") == -1:
        data = receiveResponseData(message,method,domain,url)
        response = data.decode(decoder)
        print(response)
    else:
        #Get file name and extension and folder path
        file_name = url.split("/").pop()
        extension = file_name.partition(".")[2]
        path = url.partition("http://" + domain)[2].partition("/" + file_name)[0]

        #Check if the image is supported
        if extension not in supported_img:
            data = receiveResponseData(message, method, domain, url)
            response = data.decode(decoder)
            print(response)
            return

        try:
            #No folder for caching (no data cached)
            os.makedirs("cache/" + domain + "/" + path)
            data = receiveResponseData(message,method,domain,url)
            response = data.decode(decoder)

            saveCacheImages(response,domain,path,file_name)
        except:
            #Folder path found
            #Check for the cache file validity
            try:
                #Check for cached file existing
                cache_img = open("cache/" + domain + "/" + path + "/" + file_name, "rb")
                cache_img.close()
                cache_img_header = open("cache/" + domain + "/" + path + "/" + file_name.partition(".")[0] + ".bin", "rb")
                cache_img_header.close()
                cache_header = cache_img_header.read().decode(decoder)

                #Get last cache time stamp
                header,blank,timecheck = cache_header.partition("\r\n\r\n")
                dd,mm,yy,hh,mm,ss = timecheck.split("/")
                getdate = datetime(yy,mm,dd,hh,mm,ss) + timedelta(seconds=cache_time)

                #Test for validity
                if getdate > datetime.now():
                    raise TypeError() #Cancel cache to write new cache

                #Write valid cache and send back to client
                response = header + "\r\n\r\n"+ cache_img.read().decode(decoder)
                data = response.encode(decoder)

            except:
                #No data cached found or cache file expires
                #Pushing the request to the web server
                data = receiveResponseData(message,method,domain,url)
                response = data.decode(decoder)
                saveCacheImages(response,domain,path,file_name)
    return data

########################################### METHOD PROCESSSING ########################################################

def methodProcessing(message,client):
    try:
        #Get information
        method = message.split()[0]
        url = message.split()[1]
        domain = message.split()[4]
    except:
        print("No data received")
        return

    #Test for valid methods
    if method not in ("GET","POST","HEAD"):
            return403(client)
            return #403

    #Test for whitelisted websites
    if WLenabled:
        if domain not in whitelist:
            print("Not available")
            return403(client)
            return #403

    ##################### GO TO WRITE RECEIVE DATA IF GONE WRONG ########################
    data = createCacheData(message,method,domain,url)
    #####################################################################################
    response = data.decode(decoder)

    #Send the data to the client
    client.send(data)

    print("Data received: ")
    whole = response.split("\r\n")
    for i in whole:
        if len(i) == 0:
            break
        print()

def connectionProcessing(client):
    #Receiving data
    msg = client.recv(buffer_size)
    
    # Test for restricted access time
    if restriction:
        if not time(time_allow[0], 0, 0) <= datetime.now().time() <= time(time_allow[1], 0, 0):
            print("Not available")
            return403(client)
            return  # 403

    message = msg.decode(decoder)

    whole = message.split("\r\n")
    for i in whole:
        print(i)
    #Process the request
    methodProcessing(message,client)
    client.close()

    print("########################################")
    print("Connection to",addr_name,"ended! ")
    print("########################################")


############################################## PROXY MAIN #################################################################

#Initiate proxy server
proxy = socket(AF_INET,SOCK_STREAM)
proxy.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
proxy.bind(("127.0.0.1",8888))
proxy.listen(20)
print("Waiting for connections...")

#Proxy server processes
while True:
    #Accpeting and getting the address and port
    clientSock, address = proxy.accept()
    addr_name = str(address[0]) + ' : ' + str(address[1]) # 127.0.0.1 : XXXXX

    print("#################################")
    print("Connected to", addr_name)
    print("#################################")

    #Initiate threading
    main_thread = threading.Thread(name=addr_name,target=connectionProcessing,args=(clientSock,))
    main_thread.start()

    #main_thread.join()
    #connectionProcessing(clientSock,address)
print("End")
proxy.close()

