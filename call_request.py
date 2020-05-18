"""Modulo con funciones para hacer peticiones de control de llamada
"""
import socket

BUFFER_SIZE = 1024  # Tamaño del buffer para recibir respuesta a los comandos del control de llamada


def llamar(dst_user, src_nick, srcUDPport):
    """Envia una peticion CALLING a un peer y devuelve su respuesta
        IN:
            - dst_user: lista con la direccion y puerto TCP del peer
            - src_nick: nick del usuario origen del cliente
            - srcUDPport: puerto UDP donde el usuario del cliente quiere recibir el video
        OUT: respuesta del peer parseada en una lista
    """
    mensaje = 'CALLING ' + src_nick + ' ' + str(srcUDPport)
    print("--> " + mensaje)
    resp = tcp_conn(mensaje, dst_user[0], dst_user[1], resp=True)
    print("<-- " + resp)
    return resp.split(" ")


def pausar(dst_user, src_nick):
    """Envia una peticion CALL_HOLD a un peer
        IN:
            - dst_user: lista con la direccion y puerto TCP del peer
            - src_nick: nick del usuario origen del cliente
    """
    mensaje = 'CALL_HOLD ' + src_nick
    print("--> " + mensaje)
    tcp_conn(mensaje, dst_user[0], dst_user[1])


def reanudar(dst_user, src_nick):
    """Envia una peticion CALL_RESUME a un peer
        IN:
            - dst_user: lista con la direccion y puerto TCP del peer
            - src_nick: nick del usuario origen del cliente
    """
    mensaje = 'CALL_RESUME ' + src_nick
    print("--> " + mensaje)
    tcp_conn(mensaje, dst_user[0], dst_user[1])


def finalizar(dst_user, src_nick):
    """Envia una peticion CALL_END a un peer
        IN:
            - dst_user: lista con la direccion y puerto TCP del peer
            - src_nick: nick del usuario origen del cliente
    """
    mensaje = 'CALL_END ' + src_nick
    print("--> " + mensaje)
    try:
        tcp_conn(mensaje, dst_user[0], dst_user[1])
    except ConnectionRefusedError:
        pass


def tcp_conn(mensaje, direccion, puerto, resp=False):
    """Procesa una peticion a un peer con el mensaje especificado, devolviendo su respuesta si la hay
        IN:
            - mensaje: mensaje a ser enviado al peer
            - direccion: direccion del peer a quien va dirigido
            - puerto: puerto del peer a quien va dirigido
            - resp: indicar a True si el peer deberia enviar una respuesta
        OUT: respuesta del peer si la hay
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((direccion, int(puerto)))
    s.sendall(bytes(mensaje, encoding='utf8'))
    if resp:
        data = s.recv(BUFFER_SIZE)
        s.close()
        return data.decode()
    else:
        s.close()
