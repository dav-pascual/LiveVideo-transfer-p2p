import socket

BUFFER_SIZE = 1024


def llamar(dst_user, src_nick, srcUDPport):
    mensaje = 'CALLING ' + src_nick + ' ' + srcUDPport
    resp = tcp_conn(mensaje, dst_user[0], dst_user[1], resp=True)
    print("calling: " + resp)
    return resp.split(" ")


def pausar(dst_user, src_nick):
    mensaje = 'CALL_HOLD ' + src_nick
    resp = tcp_conn(mensaje, dst_user[0], dst_user[1])
    print("request CALL_HOLD")


def reanudar(dst_user, src_nick):
    mensaje = 'CALL_RESUME ' + src_nick
    resp = tcp_conn(mensaje, dst_user[0], dst_user[1])
    print("request CALL_RESUME")


def finalizar(dst_user, src_nick):
    mensaje = 'CALL_END ' + src_nick
    resp = tcp_conn(mensaje, dst_user[0], dst_user[1])
    print("request CALL_END")


def tcp_conn(mensaje, direccion, puerto, resp=False):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((direccion, puerto))
    s.sendall(bytes(mensaje, encoding='utf8'))
    if resp:
        data = s.recv(BUFFER_SIZE)
        s.close()
        return data.decode()
    else:
        s.close()
