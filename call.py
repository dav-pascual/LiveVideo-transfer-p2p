import socket


class Call(object):

    def __init__(self, dst_ip, dst_port):
        # Inicializamos parametros de la llamada
        self.pause = False
        self.id_send = 0
        self.dst_ip = dst_ip
        self.dst_port = dst_port

        # Abrimos socket de envio
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def inc_idsend(self):
        self.id_send += 1

    def enviar_frame(self, mensaje):
        self.send_socket.sendto(mensaje, (self.dst_ip, self.dst_port))
