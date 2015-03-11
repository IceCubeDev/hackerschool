__author__ = 'Ivan Dortulov'

import tkinter as tk
import tkinter.filedialog
import tkinter.ttk
import socket


class Application(tk.Frame):

    def __init__(self, root):

        tk.Frame.__init__(self, root)

        self.connected = False
        self.socket = None

        # options for buttons
        self.button_opt = {'fill': tk.BOTH, 'padx': 5, 'pady': 5}

        # define options for opening or saving a file
        self.file_opt = options = {}
        options['defaultextension'] = '.html'
        options['filetypes'] = [('all files', '.*'), ('html files', '.html')]
        options['initialdir'] = 'C:\\'
        options['initialfile'] = ''
        options['parent'] = root
        options['title'] = 'Please select a file'

        self.create_widgets()

    def create_widgets(self):
        self.grid()

        self.address_input = tk.Entry(self)
        self.address_input.grid(column=0,row=0,sticky='EW')

        self.connect_button = tk.Button(self,text=u"Connect!")
        self.connect_button.grid(column=1,row=0)
        self.connect_button["command"] = self.handle_connect_button

        self.connection_status = tk.Label(self, anchor="w",fg="red", text="NOT CONNECTED")
        self.connection_status.grid(column=3,row=0)

        self.input_label = tk.Label(self, anchor="w", fg="black", text="Input")
        self.input_label.grid(column=0, row=1)

        self.request_input = tk.Text(self, height=10)
        self.request_input.grid(column=0,row=2,sticky='NSEW',columnspan=2)

        self.submit_button = tk.Button(self, text=u"Submit")
        self.submit_button.grid(column=3,row=2)
        self.submit_button["command"] = self.handle_submit

        self.file_input = tk.Entry(self)
        self.file_input.grid(column=0,row=3, sticky='EW')

        self.browse_button = tk.Button(self, text=u"Browse...")
        self.browse_button.grid(column=1,row=3)
        self.browse_button["command"] = self.ask_open_file

        self.output_label = tk.Label(self, anchor="w", fg="black", text="Output")
        self.output_label.grid(column=0,row=4)

        self.response = tk.Text(self, height=10)
        self.response.grid(column=0,row=5,sticky='NW',columnspan=2)
        self.response.config(state=tk.DISABLED)

        self.download_bar = tk.ttk.Progressbar(orient=tk.HORIZONTAL, mode='determinate', length=645)
        self.download_bar.grid(column=0, row=6, sticky="W")

        self.grid_columnconfigure(0,weight=1)
        self.update()
        #self.resizable(True, True)
        #self.geometry(self.geometry())

    def handle_connect_button(self):

        if not self.connected:
            try:
                address = self.address_input.get()
                if len(address) > 0:
                    ip = address[:address.find(":")]
                    port = int(address[address.find(":")+1:])
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.connect((ip, port))
                    self.socket.setblocking(0)
            except socket.error:
                pass
            else:
                self.connect_button["text"] = "Disconnect"
                self.connection_status["text"] = "CONNECTED"
                self.connection_status.config(fg="green")
                self.connected = True
        else:
            self.socket.close()
            self.socket = None
            self.connect_button["text"] = "Connect"
            self.connection_status["text"] = "NOT CONNECTED"
            self.connection_status.config(fg="red")
            self.connected = False

    def handle_submit(self):
        data = self.request_input.get("1.0", tk.END)
        data = data[:len(data) - 1]
        if self.connected:
            self.socket.sendall(data.encode())

        while True:
            data = self.socket.recv(1024)

            if len(data) == 0:
                break

            self.response.insert(tk.END, data.decode())

    def ask_open_file(self):
        file = tk.filedialog.askopenfile(mode='r', **self.file_opt)
        self.file_input.delete(0, tk.END)
        self.file_input.insert(0, file.name)

test = Application(tk.Tk())
test.mainloop()