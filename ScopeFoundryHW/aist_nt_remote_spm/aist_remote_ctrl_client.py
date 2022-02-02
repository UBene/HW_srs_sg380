'''
Created on Nov 26, 2021

@author: Benedikt Ursprung
'''

import socket

def make_client(HOST = '0.0.0.0', PORT = 54321):
    address = (HOST, PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(address)    
    return client




if __name__ == '__main__':
    client = make_client(HOST = 'localhost', PORT = 54321)
    #message = b'CIceServer'
    #client.send(message)
    h = client.recv(40)
    print(h)
    a = bytearray(h[4:])
    print([a[i] for i  in range(len(a))])
    
    
    