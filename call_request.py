import socket
import logging

BUFFER_SIZE = 1024


def llamar(dst_user, src_nick, srcUDPport):
    mensaje = 'CALLING ' + src_nick + ' ' + str(srcUDPport)
    print("--> " + mensaje)
    resp = tcp_conn(mensaje, dst_user[0], dst_user[1], resp=True)
    print("<-- " + resp)
    return resp.split(" ")


def pausar(dst_user, src_nick):
    mensaje = 'CALL_HOLD ' + src_nick
    print("--> " + mensaje)
    tcp_conn(mensaje, dst_user[0], dst_user[1])


def reanudar(dst_user, src_nick):
    mensaje = 'CALL_RESUME ' + src_nick
    print("--> " + mensaje)
    tcp_conn(mensaje, dst_user[0], dst_user[1])


def finalizar(dst_user, src_nick):
    mensaje = 'CALL_END ' + src_nick
    print("--> " + mensaje)
    try:
        tcp_conn(mensaje, dst_user[0], dst_user[1])
    except ConnectionRefusedError:
        pass


def tcp_conn(mensaje, direccion, puerto, resp=False):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((direccion, int(puerto)))
    s.sendall(bytes(mensaje, encoding='utf8'))
    if resp:
        data = s.recv(BUFFER_SIZE)
        s.close()
        return data.decode()
    else:
        s.close()
