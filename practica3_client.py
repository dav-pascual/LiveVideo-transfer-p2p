# import the library
from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import cv2
import ds_request


class VideoClient(object):
    user_nickname = None
    user_ip = None
    user_port = 0

    def __init__(self, window_size, user_nickname, user_ip, user_port):
        # Inicializamos datos del usuario
        self.user_nickname = user_nickname
        self.user_ip = user_ip
        self.user_port = user_port

        # Creamos una variable que contenga el GUI principal
        self.app = gui("Redes2 - P2P", window_size)
        self.app.setGuiPadding(10, 10)

        # Preparación del interfaz
        self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 ")
        self.app.addImage("video", "imgs/webcam.gif")

        # Registramos la función de captura de video
        # Esta misma función también sirve para enviar un vídeo
        self.cap = cv2.VideoCapture(0)
        self.app.setPollTime(20)
        self.app.registerEvent(self.capturaVideo)

        # Añadir los botones
        self.app.addButtons(["Conectar", "Colgar", "Cambiar Nick", "Salir"], self.buttonsCallback)

        # Barra de estado
        # Debe actualizarse con información útil sobre la llamada (duración, FPS, etc...)
        self.app.addStatusbar(fields=2)

    def start(self):
        self.app.go()

    # Función que captura el frame a mostrar en cada momento
    def capturaVideo(self):

        # Capturamos un frame de la cámara o del vídeo
        ret, frame = self.cap.read()
        frame = cv2.resize(frame, (640, 480))
        cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

        # Lo mostramos en el GUI
        self.app.setImageData("video", img_tk, fmt='PhotoImage')

    # Aquí tendría que el código que envia el frame a la red
    # ...

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

    # Función que gestiona los callbacks de los botones
    def buttonsCallback(self, button):
        if button == "Salir":
            # Salimos de la aplicación
            self.app.stop()
        elif button == "Conectar":
            # Entrada del nick del usuario a conectar
            nick = self.app.textBox("Conexión",
                                    "Introduce el nick del usuario a buscar")
        elif button == "Cambiar Nick":
            new_nick = self.app.stringBox("new_nick", "Nuevo nick")
            password = self.app.stringBox("password", "Contraseña")
            user_reg = ds_request.register(new_nick, password, self.user_ip, self.user_port)
            if user_reg[0] == 'OK':
                self.app.infoBox("registered", "Cambio de nick correcto")
                self.user_nickname = new_nick
            else:
                if user_reg[1] == 'WRONG_PASS':
                    self.app.errorBox("wrong_pass", "¡El usuario ya existe!")
                else:
                    self.app.errorBox("syntax_error", "Los campos no se han rellenado correctamente.")


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
        self.app.addLabel("user_port", "Puerto:", 4, 0)
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
                    self.app.errorBox("wrong_pass", "¡El usuario ya existe!")
                    self.app.clearEntry("userEnt")
                    self.app.clearEntry("passEnt")
                    self.app.setFocus("userEnt")
                else:
                    self.app.errorBox("syntax_error", "Rellene los campos correctamente.")
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
                        self.app.errorBox("wrong_pass", "¡Contraseña incorrecta!")
                        self.app.clearEntry("userEnt2")
                    else:
                        self.app.errorBox("syntax_error", "Rellene los campos correctamente.")
            else:
                self.app.errorBox("not_found", "¡El usuario no ha sido encontrado!")
                self.app.clearEntry("userEnt2")
                self.app.clearEntry("passEnt2")
                self.app.setFocus("userEnt2")


if __name__ == '__main__':
    rg = Access()
    rg.start()

    # Crear aquí los threads de lectura, de recepción y,
    # en general, todo el código de inicialización que sea necesario
    # ...

    # Lanza el bucle principal del GUI
    # El control ya NO vuelve de esta función, por lo que todas las
    # acciones deberán ser gestionadas desde callbacks y threads
