import socket
import bisect

MAX_UDP_BUFFER = 65507
TCP_BUFFER = 1024


class Call(object):

    def __init__(self, src_ip, srcUDPport, dst_ip, dstUDPport, dstTCPport):
        # Inicializamos parametros de la llamada
        self.finalizar = False
        self.pause = False
        self.buffering = True
        self.buffer_size = 20
        self.id_send = 0
        self.src_ip = src_ip
        self.srcUDPport = srcUDPport
        self.dst_ip = dst_ip
        self.dstUDPport = dstUDPport
        self.dstTCPport = dstTCPport

        # Abrimos socket UDP de envio de video
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Abrimos socket UDP de recepcion de video
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recv_sock.bind((self.src_ip, self.srcUDPport))

        # Creamos buffer
        self.buffer = []

    def inc_idsend(self):
        self.id_send += 1

    def enviar_frame(self, mensaje):
        self.send_sock.sendto(mensaje, (self.dst_ip, int(self.dstUDPport)))

    def empty_buffer(self):
        if self.buffer:
            return False
        else:
            return True

    def recibir_frames(self):
        while not self.finalizar:
            # Recibimos frame en el socket
            data, addr = self.recv_sock.recvfrom(MAX_UDP_BUFFER)  # TODO timeout?
            if not data:
                continue
            # Extraemos campos
            vals = data.split(b'#')
            packet = {'timestamp': vals[1].decode(),
                      'resolution': vals[2].decode(),
                      'fps': vals[3].decode(),
                      'encimg': b'#'.join(vals[4:])}
            id_frame = int(vals[0].decode())
            # Si el id del paquete es menor que el siguiente a reproducirse menos uno, lo descartamos
            if not self.empty_buffer():
                if id_frame < self.buffer[0][0] - 1:
                    continue
            # Si no, insertamos el frame en el buffer ordenado, como una tupla (id, frame_dict)
            bisect.insort(self.buffer, (id_frame, packet))
            # Si hemos llenado el buffer al tamaño deseado ponemos buffering a False
            if self.buffering and len(self.buffer) >= self.buffer_size:
                self.buffering = False

    def finalizar_sesion(self):
        self.finalizar = True
        self.send_sock.close()
        self.recv_sock.close()
