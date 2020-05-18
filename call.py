"""Modulo que contiene la clase Call para llamadas
"""
import socket
import bisect
from time import time

MAX_UDP_BUFFER = 65507  # Tamaño maximo del buffer UDP (MTU)


class Call(object):
    """Clase que es instanciada cada vez que hay una llamada, y que contiene datos referentes a esta
    """

    def __init__(self, src_ip, srcUDPport, srcTCPport, dst_ip, dstUDPport, dstTCPport):
        """Inicializacion de parametros de llamada y apertura de sockets
           IN:
                - src_ip: IP origin de la llamada (este cliente)
                - srcUDPport: puerto IP donde el cliente envía y recibe el video.
                - srcTCPport: puerto donde el cliente recibe comandos de control del otro peer
                - dst_ip: IP del otro peer de la llamada
                - dstUDPport: puerto donde el otro peer de la llamada recibe el video
                - dstTCPport: puerto donde el otro peer recibe comandos de control de llamada
        """
        # Inicializamos parametros de la llamada
        self.finalizar = False
        self.pause = False
        self.buffering = True
        self.buffer_size = 10           # Tamaño del buffer
        self.id_send = 0                # Id del paquete a enviar
        self.src_ip = src_ip
        self.srcUDPport = srcUDPport
        self.dst_ip = dst_ip
        self.dstUDPport = dstUDPport
        self.srcTCPport = srcTCPport
        self.dstTCPport = dstTCPport
        self.fps_adjust = 0             # Parametro de ajuste de FPS
        self.res = "HIGH"
        self.new_res = False

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
        """Incrementa el id del paquete del frame a enviar
        """
        self.id_send += 1

    def enviar_frame(self, mensaje):
        """Envia paquete del frame al peer
        """
        self.send_sock.sendto(mensaje, (self.dst_ip, int(self.dstUDPport)))

    def empty_buffer(self):
        """Retorna True si el buffer esta vacio,
           False si no"""
        if self.buffer:
            return False
        else:
            return True

    def recibir_frames(self, setImageResolution):
        """Metodo de hilo que recibe frames enviados por el otro peer
        """
        while not self.finalizar:
            # Recibimos frame en el socket
            data, addr = self.recv_sock.recvfrom(MAX_UDP_BUFFER)
            # Automensaje de que la llamada ha terminado
            if data == b'STOP':
                break
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
            buffer_len = len(self.buffer)
            if self.buffering and buffer_len >= self.buffer_size:
                self.buffering = False

            # Parametro de ajuste de FPS para mantener el buffer constante
            if buffer_len > 35:
                self.fps_adjust = 10
            elif 20 < buffer_len <= 30:
                self.fps_adjust = 5
            elif buffer_len < 5:
                self.fps_adjust = -5
            elif 10 <= buffer_len <= 15:
                self.fps_adjust = 0

            # Control de congestion
            # Ajusta la resolucion de envio segun el retardo de recepcion
            delay = time() - float(packet['timestamp'])
            if delay >= 0.4 and self.res != "LOW":
                self.res = "LOW"
                self.new_res = True
            elif delay <= 0.2 and self.res != "HIGH":
                self.res = "HIGH"
                self.new_res = True
            elif 0.2 < delay < 0.4 and self.res != "MEDIUM":
                self.res = "MEDIUM"
                self.new_res = True

    def finalizar_sesion(self, recv_th):
        """Rompe el loop del hilo de recibir frames y cierra sockets
        """
        # Rompemos el loop de recibir frames y cerramos sockets
        self.finalizar = True
        self.send_sock.sendto(b'STOP', (self.src_ip, int(self.srcUDPport)))
        if recv_th.is_alive():
            recv_th.join()
        self.recv_sock.close()
        self.send_sock.close()
