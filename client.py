import base64
import io
import os
import threading

from socket import socket, AF_INET, SOCK_STREAM

from customtkinter import *
from tkinter import filedialog

from PIL import Image

set_appearance_mode("dark")


SERVER_IP = "192.168.0.222"
SERVER_PORT = 8080


class MainWindow(CTk):

    def __init__(self):

        super().__init__()

        self.geometry("900x600")

        self.title("Chat Client")

        self.username = "User"

        self.images = []

        self.connected = False

        # SOCKET

        try:

            self.sock = socket(AF_INET, SOCK_STREAM)

            self.sock.connect(
                (SERVER_IP, SERVER_PORT)
            )

            self.connected = True

            print("ПІДКЛЮЧЕНО ДО СЕРВЕРА")

        except Exception as e:

            print("CONNECTION ERROR:", e)

        # CHAT

        self.chat_field = CTkScrollableFrame(self)

        self.chat_field.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # INPUT FRAME

        self.bottom_frame = CTkFrame(self)

        self.bottom_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        # MESSAGE ENTRY

        self.message_entry = CTkEntry(
            self.bottom_frame,
            placeholder_text="Введіть своє повідомлення..."
        )

        self.message_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        self.message_entry.bind(
            "<Return>",
            lambda e: self.send_message()
        )

        # SEND BUTTON

        self.send_button = CTkButton(
            self.bottom_frame,
            text="➤",
            width=60,
            command=self.send_message
        )

        self.send_button.pack(
            side="left",
            padx=5
        )

        # IMAGE BUTTON

        self.image_button = CTkButton(
            self.bottom_frame,
            text="📂",
            width=60,
            command=self.open_image
        )

        self.image_button.pack(
            side="left",
            padx=5
        )

        # NAME ENTRY

        self.name_entry = CTkEntry(
            self,
            placeholder_text="Ваш нік"
        )

        self.name_entry.place(x=10, y=10)

        self.name_button = CTkButton(
            self,
            text="Зберегти",
            command=self.save_name
        )

        self.name_button.place(x=170, y=10)

        # THREAD

        if self.connected:

            threading.Thread(
                target=self.recv_message,
                daemon=True
            ).start()

        else:

            self.add_message(
                "Немає підключення до сервера"
            )

    def save_name(self):

        new_name = self.name_entry.get().strip()

        if new_name:

            self.username = new_name

            self.add_message(
                f"Ваш новий нік: {self.username}"
            )

    def add_message(self, message, img=None):

        frame = CTkFrame(
            self.chat_field,
            fg_color="gray20"
        )

        frame.pack(
            pady=5,
            padx=5,
            anchor="w"
        )

        if img:

            self.images.append(img)

            label = CTkLabel(
                frame,
                text=message,
                image=img,
                compound="top"
            )

        else:

            label = CTkLabel(
                frame,
                text=message,
                wraplength=600,
                justify="left"
            )

        label.pack(
            padx=10,
            pady=10
        )

    def send_message(self):

        if not self.connected:

            self.add_message(
                "Немає з'єднання"
            )

            return

        message = self.message_entry.get().strip()

        if not message:
            return

        data = f"TEXT@{self.username}@{message}\n"

        try:

            self.sock.sendall(
                data.encode()
            )

            self.add_message(
                f"Ви: {message}"
            )

        except Exception as e:

            print("SEND ERROR:", e)

            self.add_message(
                f"Помилка: {e}"
            )

        self.message_entry.delete(0, END)

    def recv_message(self):

        buffer = ""

        while True:

            try:

                chunk = self.sock.recv(4096)

                if not chunk:

                    self.add_message(
                        "Сервер відключився"
                    )

                    break

                buffer += chunk.decode(
                    "utf-8",
                    errors="ignore"
                )

                while "\n" in buffer:

                    line, buffer = buffer.split("\n", 1)

                    self.handle_line(
                        line.strip()
                    )

            except Exception as e:

                print("RECV ERROR:", e)

                self.add_message(
                    f"Помилка отримання: {e}"
                )

                break

    def handle_line(self, line):

        if not line:
            return

        parts = line.split("@", 3)

        msg_type = parts[0]

        # TEXT

        if msg_type == "TEXT":

            if len(parts) >= 3:

                author = parts[1]

                message = parts[2]

                self.add_message(
                    f"{author}: {message}"
                )

        # IMAGE

        elif msg_type == "IMAGE":

            if len(parts) >= 4:

                author = parts[1]

                filename = parts[2]

                b64_img = parts[3]

                try:

                    img_data = base64.b64decode(
                        b64_img
                    )

                    pil_img = Image.open(
                        io.BytesIO(img_data)
                    )

                    ctk_img = CTkImage(
                        pil_img,
                        size=(300, 300)
                    )

                    self.add_message(
                        f"{author} надіслав фото: {filename}",
                        img=ctk_img
                    )

                except Exception as e:

                    self.add_message(
                        f"Помилка картинки: {e}"
                    )

    def open_image(self):

        if not self.connected:

            self.add_message(
                "Немає з'єднання"
            )

            return

        file_name = filedialog.askopenfilename()

        if not file_name:
            return

        try:

            with open(file_name, "rb") as f:

                raw = f.read()

            b64_data = base64.b64encode(raw).decode()

            short_name = os.path.basename(
                file_name
            )

            data = (
                f"IMAGE@{self.username}"
                f"@{short_name}@{b64_data}\n"
            )

            self.sock.sendall(
                data.encode()
            )

            img = CTkImage(
                light_image=Image.open(file_name),
                size=(300, 300)
            )

            self.add_message(
                "Ви надіслали фото",
                img=img
            )

        except Exception as e:

            print("IMAGE ERROR:", e)

            self.add_message(
                f"Помилка: {e}"
            )


if __name__ == "__main__":

    app = MainWindow()

    app.mainloop()
