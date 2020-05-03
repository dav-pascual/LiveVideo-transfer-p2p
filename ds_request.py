import socket

DS_ADRESS = 'vega.ii.uam.es'
DS_PORT = 8000
BUFFER_SIZE = 1024
VERSION = 'V0'


def register(nick, password, user_ip, user_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((DS_ADRESS, DS_PORT))
    mensaje = 'REGISTER ' + nick + ' ' + user_ip + ' ' + user_port + ' ' + password + ' ' + VERSION
    s.send(bytes(mensaje, encoding='utf8'))
    data = s.recv(BUFFER_SIZE)
    s.close()
    print("register: " + data.decode())
    return data.decode().split(" ")


def query_user(nick):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((DS_ADRESS, DS_PORT))
    mensaje = 'QUERY ' + nick
    s.send(bytes(mensaje, encoding='utf8'))
    data = s.recv(BUFFER_SIZE)
    s.close()
    print("query_user:" + data.decode())
    return data.decode().split(" ")
