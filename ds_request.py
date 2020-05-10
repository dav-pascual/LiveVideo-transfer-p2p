import socket

DS_ADRESS = 'vega.ii.uam.es'
DS_PORT = 8000
BUFFER_SIZE = 1024
VERSION = 'V0'


def register(nick, password, user_ip, user_port):
    mensaje = 'REGISTER ' + nick + ' ' + user_ip + ' ' + user_port + ' ' + password + ' ' + VERSION
    resp = tcp_conn(mensaje)
    print("register: " + resp)
    return resp.split(" ")


def query_user(nick):
    mensaje = 'QUERY ' + nick
    resp = tcp_conn(mensaje)
    print("query_user: " + resp)
    return resp.split(" ")


def list_users():
    mensaje = 'LIST_USERS'
    resp = tcp_conn(mensaje, users=True)
    users = resp.split("#")                   # Separamos los usuarios con el delimitador
    del users[-1]                             # Eliminamos ultimo elemento vacio
    first_elem = users[0].split(" ")
    info = first_elem[:3]                     # Extraemos info de la respuesta del primer elem
    users[0] = ' '.join(first_elem[3:])       # Eliminamos esta info de la lista users
    print("list_users: " + ' '.join(info))
    return info, users


def tcp_conn(mensaje, users=False):
    if not users:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((DS_ADRESS, DS_PORT))
        s.sendall(bytes(mensaje, encoding='utf8'))
        data = s.recv(BUFFER_SIZE)
        return data.decode()
    else:
        # En caso de que queramos recibir una lista de usuarios separados con '#'
        total_data = ''
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((DS_ADRESS, DS_PORT))
        s.sendall(bytes(mensaje, encoding='utf8'))

        data = s.recv(BUFFER_SIZE)
        current_data = data.decode()
        total_data += current_data
        # Obtenemos numero de usuarios del primer elemento
        tam = int(current_data.split(" ")[2])
        while True:
            data = s.recv(BUFFER_SIZE)
            current_data = data.decode()
            total_data += current_data
            # Si tenemos ya todos los usuarios esperados dejamos de recibir
            if len(total_data.split("#")) - 1 >= tam:
                break
            # if len(data) < BUFFER_SIZE:
            #     break
        s.close()
        return total_data
