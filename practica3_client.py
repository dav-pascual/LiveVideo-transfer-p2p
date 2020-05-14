# import the library
from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import cv2
import ds_request
import call_request
from call import Call
from time import time, sleep
import socket
import threading


BUFFER_SIZE = 1024


class VideoClient(object):

    def __init__(self, window_size, user_nickname, user_ip, tcp_port):
        # Inicializamos datos del usuario
        self.user_nickname = user_nickname
        self.user_ip = user_ip
        self.tcp_port = int(tcp_port)
        self.udp_port = 8080
        self.llamada = None
        self.version = 'V0'

        # Creamos una variable que contenga el GUI principal
        self.app = gui("Redes2 - P2P", window_size)
        self.app.setGuiPadding(10, 10)

        # Preparación del interfaz
        self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 ")
        self.app.addImage("video", "imgs/webcam.gif")

        # Registramos la función de captura de video
        # Esta misma función también sirve para enviar un vídeo
        # VideoCapture object
        self.cap = cv2.VideoCapture(0)
        # self.app.setPollTime(20)
        # self.app.registerEvent(self.capturaVideo)

        # Definimos hilos
        self.exit_flag = False
        # Hilo de mostrar video en GUI y enviarlo
        self.myVideo_th = threading.Thread(target=self.capturaVideo)
        self.myVideo_th.daemon = True
        self.myVideo_th.start()
        # Hilo de recibir video
        self.recvVideo_th = None
        # Hilo de mostrar video recibido almacenado en buffer
        self.bufferVideo_th = None
        self.play_flag = False
        # Hilo de atender comandos de control
        self.callCtrl_th = threading.Thread(target=self.call_control)
        self.callCtrl_th.daemon = True
        self.callCtrl_th.start()

        # Añadir los botones
        self.app.addButtons(["Colgar", "Pausar", "Reanudar", "Conectar", "Usuarios",
                             "Buscar", "Cambiar Nick", "Salir"], self.buttonsCallback)
        self.app.hideButton("Pausar")
        self.app.hideButton("Reanudar")
        self.app.hideButton("Colgar")

        # Definición subventana del video del peer de la llamada
        with self.app.subWindow("peer", size="640x500"):
            self.app.addImage("video_peer", "imgs/webcam2.gif")

        # Definición subventana listar usuarios
        with self.app.subWindow("Usuarios", size="500x470"):
            self.app.label("Lista de usuarios")
            self.app.getLabelWidget("Lista de usuarios").config(font=("Sans Serif", "16", "bold"))
            self.app.label("Selecciona uno para establecer una conexión:")
            self.app.addListBox("users", [])
            self.app.setListBoxWidth("users", 30)
            self.app.setListBoxHeight("users", 18)
            self.app.setListBoxMulti("users", multi=False)
            self.app.addButtons(["Seleccionar"], self.buttonsCallback)

        # Barra de estado
        # Debe actualizarse con información útil sobre la llamada (duración, FPS, etc...)
        self.app.addStatusbar(fields=2)

    def start(self):
        self.app.go()

    # Función que captura el frame a mostrar en cada momento y lo envia en caso de que haya una llamada en curso
    def capturaVideo(self):
        while not self.exit_flag:
            # Capturamos un frame de la cámara o del vídeo
            ret, frame = self.cap.read()
            frame = cv2.resize(frame, (640, 480))
            cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

            # Lo mostramos en el GUI
            self.app.setImageData("video", img_tk, fmt='PhotoImage')

            # Si hay una llamada enviamos el frame
            if self.llamada is not None and not self.llamada.pause:
                # Compresión JPG al 50% de resolución
                encode_param = [cv2.IMWRITE_JPEG_QUALITY, 50]
                result, encimg = cv2.imencode('.jpg', frame, encode_param)
                if not result:
                    print('Error al codificar imagen')
                encimg = encimg.tobytes()

                # Creamos el mensaje y enviamos
                cabecera = "{}#{}#{}#{}#".format(str(self.llamada.id_send), str(time()), "640x480", "20")
                self.llamada.inc_idsend()
                payload = bytes(cabecera, encoding='utf8') + encimg
                self.llamada.enviar_frame(payload)

            # Los frames se obtienen (y envian) con cierto intervalo
            sleep(0.025)

    def reproducirVideo(self):
        while self.play_flag:
            if not self.llamada.buffering:
                if not self.llamada.empty_buffer():
                    frame = self.llamada.buffer.pop(0)[1]
                    encimg = frame['encimg']
                    # Descompresión de los datos, una vez recibidos
                    decimg = cv2.imdecode(np.frombuffer(encimg, np.uint8), 1)
                    # Conversión de formato para su uso en el GUI
                    cv2_im = cv2.cvtColor(decimg, cv2.COLOR_BGR2RGB)
                    img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))
                    # Lo mostramos en el GUI
                    self.app.setImageData("video_peer", img_tk, fmt='PhotoImage')
            sleep(0.05)

    # Establece la resolución de la imagen capturada
    def setImageResolution(self, resolution):
        # Se establece la resolución de captura de la webcam
        # Puede añadirse algún valor superior si la cámara lo permite
        # pero no modificar estos
        if resolution == "LOW":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
        elif resolution == "MEDIUM":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        elif resolution == "HIGH":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def iniciar_llamada(self, dst_ip, dstTCPport, dstUDPport, rcv=False):
        if self.llamada is None or rcv:
            self.llamada = Call(self.user_ip, self.udp_port, dst_ip, dstUDPport, dstTCPport)
        else:
            self.app.errorBox("BUSY", "¡Ya hay una llamada en curso!")
            return

        # Abrimos subventana para mostrar video del peer
        self.app.openSubWindow("peer")
        self.app.showSubWindow("peer")

        # Hilo de recibir video
        self.recvVideo_th = threading.Thread(target=self.llamada.recibir_frames)
        self.recvVideo_th.start()
        # Hilo de mostrar video recibido almacenado en buffer
        self.play_flag = True
        self.bufferVideo_th = threading.Thread(target=self.reproducirVideo)
        self.bufferVideo_th.start()

        self.app.hideButton("Conectar")
        self.app.hideButton("Usuarios")
        self.app.hideButton("Buscar")
        self.app.hideButton("Cambiar Nick")
        self.app.showButton("Pausar")
        self.app.showButton("Colgar")

    def finalizar_llamada(self):
        # Dejamos de mostrar video recibido
        self.play_flag = False
        sleep(0.1)
        # Dejamos de recibir video, cerramos socket y eliminamos referencia a la llamada
        self.llamada.finalizar_sesion()
        self.llamada = None
        # Volvemos al estado de GUI normal
        self.app.hideSubWindow("peer", useStopFunction=True)
        self.app.stopSubWindow()
        self.app.hideButton("Pausar")
        self.app.hideButton("Reanudar")
        self.app.hideButton("Colgar")
        self.app.showButton("Conectar")
        self.app.showButton("Usuarios")
        self.app.showButton("Buscar")
        self.app.showButton("Cambiar Nick")

    def call_control(self):
        # Abrimos socket TCP de recepcion de comandos de control
        control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        control_sock.bind((self.user_ip, self.tcp_port))
        control_sock.listen(1)

        while True:
            connection, client_address = control_sock.accept()
            try:
                data = connection.recv(BUFFER_SIZE)  # TODO timeout?
                if not data:
                    continue
                current_data = data.decode()
                print("<-- " + current_data)
                command = current_data.split(" ")
                if command[0] == "CALLING":
                    user_query = ds_request.query_user(command[1])
                    if user_query[0] == 'OK' and self.version in user_query[5].split("#"):
                        if self.llamada is None:
                            mensaje = "CALL_ACCEPTED " + self.user_nickname + " " + str(self.udp_port)
                            print("--> " + mensaje)
                            connection.sendall(bytes(mensaje, encoding='utf8'))
                            self.iniciar_llamada(user_query[3], user_query[4], command[2], rcv=True)
                        else:
                            mensaje = "CALL_BUSY"
                            print("--> " + mensaje)
                            connection.sendall(bytes(mensaje, encoding='utf8'))
                    else:
                        mensaje = "CALL_DENIED " + self.user_nickname
                        print("--> " + mensaje)
                        connection.sendall(bytes(mensaje, encoding='utf8'))
                elif self.llamada is not None:
                    if command[0] == "CALL_HOLD":
                        self.llamada.pause = True
                    elif command[0] == "CALL_RESUME":
                        self.llamada.pause = False
                    elif command[0] == "CALL_END":
                        self.finalizar_llamada()
                    else:
                        pass
                else:
                    pass
            finally:
                connection.close()
        control_sock.close()

    # Función que gestiona los callbacks de los botones
    def buttonsCallback(self, button):
        if button == "Salir":
            # Salimos de la aplicación
            if self.llamada:
                self.finalizar_llamada()
            self.exit_flag = True
            sleep(0.3)
            self.app.stop()
        elif button == "Conectar":
            # Entrada del nick del usuario a conectar
            nick = self.app.textBox("Conexión",
                                    "Introduce el nick del usuario a buscar")
            if not nick:
                return
            user_query = ds_request.query_user(nick)
            if user_query[0] == 'OK':
                resp = call_request.llamar(user_query[3:5], self.user_nickname, self.udp_port)
                if resp[0] == 'CALL_ACCEPTED':
                    self.iniciar_llamada(user_query[3], user_query[4], resp[2])
                elif resp[0] == 'CALL_DENIED':
                    self.app.errorBox("denied", "El usuario ha rechazado la llamada")
                elif resp[0] == 'CALL_BUSY':
                    self.app.errorBox("busy", "El usuario esta actualmente en una llamada")
            else:
                self.app.errorBox("Not found", "¡El usuario no ha sido encontrado!")
        elif button == "Cambiar Nick":
            # Entrada para cambiar de nick
            new_nick = self.app.textBox("new_nick", "Nuevo nick")
            if not new_nick:
                return
            password = self.app.textBox("password", "Contraseña")
            if not password:
                return
            user_reg = ds_request.register(new_nick, password, self.user_ip, self.tcp_port)
            if user_reg[0] == 'OK':
                self.app.infoBox("registered", "Cambio de nick correcto")
                self.user_nickname = new_nick
            else:
                if user_reg[1] == 'WRONG_PASS':
                    self.app.errorBox("Usuario existe", "¡El usuario ya existe!")
                else:
                    self.app.errorBox("Error sintaxis", "Los campos no se han rellenado correctamente.")
        elif button == "Buscar":
            # Entrada para buscar y mostrar la información de un usuario
            user = self.app.textBox("Buscar", "Buscar usuario")
            if user:
                user_query = ds_request.query_user(user)
                if user_query[0] == 'OK':
                    self.app.infoBox("User info", user_query[2:])
                else:
                    self.app.errorBox("Not found", "¡El usuario no ha sido encontrado!")
        elif button == "Usuarios":
            # Muestra en una subventana la lista de usuarios con los que poder conectarse
            info, users = ds_request.list_users()
            if info[0] == 'OK':
                self.app.openSubWindow("Usuarios")
                self.app.updateListBox("users", [i.split()[:-1] for i in users if i], select=False, callFunction=True)
                self.app.stopSubWindow()
                self.app.showSubWindow("Usuarios")
            else:
                self.app.errorBox("Error listar", "Se ha producido un error al listar los usuarios")
        elif button == "Seleccionar":
            # Obtiene el usuario seleccionado para llamar
            selected = self.app.getListBox("users")
            if not selected:
                self.app.errorBox("Error seleccion", "No se ha seleccionado ningun usuario", parent="Usuarios")
            else:
                self.app.hideSubWindow("Usuarios", useStopFunction=True)
                user_query = ds_request.query_user(selected[0][0])
                if user_query[0] == 'OK':
                    resp = call_request.llamar(user_query[3:5], self.user_nickname, self.udp_port)
                    if resp[0] == 'CALL_ACCEPTED':
                        self.iniciar_llamada(user_query[3], user_query[4], resp[2])
                    elif resp[0] == 'CALL_DENIED':
                        self.app.errorBox("denied", "El usuario ha rechazado la llamada")
                    elif resp[0] == 'CALL_BUSY':
                        self.app.errorBox("busy", "El usuario esta actualmente en una llamada")
                else:
                    self.app.errorBox("Error user", "Ha occurido un error al seleccionar el usuario")
        elif button == "Colgar":
            call_request.finalizar([self.llamada.dst_ip, self.llamada.dstTCPport], self.user_nickname)
            self.finalizar_llamada()
        elif button == "Pausar":
            call_request.pausar([self.llamada.dst_ip, self.llamada.dstTCPport], self.user_nickname)
            self.app.hideButton("Pausar")
            self.app.showButton("Reanudar")
        elif button == "Reanudar":
            call_request.reanudar([self.llamada.dst_ip, self.llamada.dstTCPport], self.user_nickname)
            self.app.hideButton("Reanudar")
            self.app.showButton("Pausar")


class Access(object):

    def __init__(self):
        self.app = gui("Redes2 - P2P - Acceso")
        self.app.setGuiPadding(10, 10)

        self.app.addLabel("registrar", "Registro", 0, 1)

        self.app.addLabel("userLab", "Nickname:", 1, 0)
        self.app.addEntry("userEnt", 1, 1)
        self.app.addLabel("passLab", "Password:", 2, 0)
        self.app.addSecretEntry("passEnt", 2, 1)
        self.app.addLabel("user_ip", "IP:", 3, 0)
        self.app.addEntry("user_ip", 3, 1)
        self.app.addLabel("user_port", "Puerto TCP:", 4, 0)
        self.app.addEntry("user_port", 4, 1)

        self.app.addButtons(["Registrarse"], self.buttonsCallback, colspan=2)

        self.app.addLabel("blank", " ", 6, 0)
        self.app.addLabel("login", "Log in", 7, 1)

        self.app.addLabel("userLab2", "Nickname:", 8, 0)
        self.app.addEntry("userEnt2", 8, 1)
        self.app.addLabel("passLab2", "Password:", 9, 0)
        self.app.addSecretEntry("passEnt2", 9, 1)

        self.app.addButtons(["Log in", "Cancelar"], self.buttonsCallback, colspan=2)

    def start(self):
        self.app.go()

    def buttonsCallback(self, button):
        if button == "Cancelar":
            self.app.stop()
        elif button == "Registrarse":
            nick = self.app.getEntry("userEnt")
            password = self.app.getEntry("passEnt")
            ip = self.app.getEntry("user_ip")
            port = self.app.getEntry("user_port")
            user_reg = ds_request.register(nick, password, ip, port)
            if user_reg[0] == 'OK':
                self.app.infoBox("registered", "Registro correcto")
                self.app.stop()
                vc = VideoClient("640x520", nick, ip, port)
                vc.start()
            else:
                if user_reg[1] == 'WRONG_PASS':
                    self.app.errorBox("Usuario existe", "¡El usuario ya existe!")
                    self.app.clearEntry("userEnt")
                    self.app.clearEntry("passEnt")
                    self.app.setFocus("userEnt")
                else:
                    self.app.errorBox("Error de sintaxis", "Rellene los campos correctamente.")
        elif button == "Log in":
            nick = self.app.getEntry("userEnt2")
            password = self.app.getEntry("passEnt2")
            user_query = ds_request.query_user(nick)
            if user_query[0] == 'OK':
                user_reg = ds_request.register(nick, password, user_query[3], user_query[4])
                if user_reg[0] == 'OK':
                    self.app.infoBox("logged", "Acceso correcto")
                    self.app.stop()
                    vc = VideoClient("640x520", nick, user_query[3], user_query[4])
                    vc.start()
                else:
                    if user_reg[1] == 'WRONG_PASS':
                        self.app.errorBox("Clave incorrecta", "¡Contraseña incorrecta!")
                        self.app.clearEntry("userEnt2")
                    else:
                        self.app.errorBox("Error campos", "Rellene los campos correctamente.")
            else:
                if user_query[1] == 'USER_UNKNOWN':
                    self.app.errorBox("User not found", "¡El usuario no existe!")
                    self.app.clearEntry("userEnt2")
                else:
                    self.app.errorBox("Error logina", "Rellene los campos correctamente.")
                self.app.clearEntry("userEnt2")
                self.app.clearEntry("passEnt2")
                self.app.setFocus("userEnt2")


if __name__ == '__main__':
    access = Access()
    access.start()

    # Crear aquí los threads de lectura, de recepción y,
    # en general, todo el código de inicialización que sea necesario
    # ...

    # Lanza el bucle principal del GUI
    # El control ya NO vuelve de esta función, por lo que todas las
    # acciones deberán ser gestionadas desde callbacks y threads
