"""Modulo con funciones para hacer peticiones al Discover Server
"""
import socket
from config import DS_ADRESS, DS_PORT, VERSION

BUFFER_SIZE = 1024  # Tamaño del buffer para recibir respuesta a los comandos al DS


def register(nick, password, user_ip, user_port):
    """Envia una peticion REGISTER al DS y devuelve su respuesta
        IN:
            - nick: nick de registro en DS
            - password: contraseña asociada al nick
            - user_ip: ip a registrar
            - user_port: puerto TCP del control de llamada a registrar
        OUT: respuesta del DS parseada en una lista
    """
    mensaje = 'REGISTER ' + nick + ' ' + user_ip + ' ' + str(user_port) + ' ' + password + ' ' + VERSION
    print("--> " + mensaje)
    resp = tcp_conn(mensaje)
    print("<-- " + resp)
    return resp.split(" ")


def query_user(nick):
    """Envia una peticion QUERY al DS y devuelve su respuesta
        IN:
            - nick: nick a consultar en DS
        OUT: respuesta del DS parseada en una lista
    """
    mensaje = 'QUERY ' + nick
    print("--> " + mensaje)
    resp = tcp_conn(mensaje)
    print("<-- " + resp)
    return resp.split(" ")


def list_users():
    """Envia una peticion LIST_USERS al DS y devuelve su respuesta
        OUT:
            - info: info de la respuesta parseada en una lista
            - users: usuarios de la respuesta parseados en una lista
    """
    mensaje = 'LIST_USERS'
    print("--> " + mensaje)
    resp = tcp_conn(mensaje, users=True)
    users = resp.split("#")                          # Separamos los usuarios con el delimitador
    # del users[-1]                                  # Eliminamos ultimo elemento vacio
    first_elem = users[0].split(" ")
    info = first_elem[:3]                            # Extraemos info de la respuesta del primer elem
    print("<-- " + ' '.join(info) + " [users...]")
    users[0] = ' '.join(first_elem[3:])              # Eliminamos esta info de la lista users
    return info, users


def tcp_conn(mensaje, users=False):
    """Procesa una peticion al DS con el mensaje especificado, devolviendo su respuesta
        IN:
            - mensaje: mensaje a ser enviado al DS
            - users: indicar True si se va a solicitar el comando LIST_USERS
        OUT: respuesta del DS
    """
    if not users:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((DS_ADRESS, DS_PORT))
        s.sendall(bytes(mensaje, encoding='utf8'))
        data = s.recv(BUFFER_SIZE)
        s.sendall(bytes("QUIT", encoding='utf8'))
        print("<-- " + s.recv(BUFFER_SIZE).decode())
        s.close()
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
        s.sendall(bytes("QUIT", encoding='utf8'))
        print("<-- " + s.recv(BUFFER_SIZE).decode())
        s.close()
        return total_data
