import socket
import threading
import time
from tkinter import Tk, Frame, Label, Button, Text, Entry, Scrollbar, PhotoImage, Listbox, StringVar
from tkinter import BOTTOM, TOP, LEFT, RIGHT, END, Y, BOTH
from tkinter.font import Font as tkfont
from tkinter.font import BOLD, ITALIC
from tkinter.filedialog import askdirectory, askopenfilename
from PIL import Image, ImageTk

# tk window basic setting: title and size###############################################
loginoutsize="400x160"
chatroomsize="800x600"
window = Tk()
window.title("Chatroom")
window.geometry(loginoutsize)
#######################################################################################

# functions#############################################################################
##global var
clientName = StringVar()
input_msg = StringVar()
msg_buf = []
listitemcounter = 0
currenttime = None
#UDP socket
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
loginFlag = 0
serverIp = "127.0.0.1"
udpServerPort = 9999
tcpServerPort = 10000
saddr = (serverIp, udpServerPort)
taddr = (serverIp, tcpServerPort)

def client_online(event=None):
    global saddr
    global clientName
    global txt_getName, entry_getName, button_getName

    '''unpack login widgets'''
    txt_getName.pack_forget()
    entry_getName.pack_forget()
    button_getName.pack_forget()
    window.unbind_all('<Return>')

    '''pack chatting room widgets & bind <enter> to <sendMsg>'''
    window.geometry(chatroomsize)
    chat = ChatRoom(window)
    window.bind("<Return>", chat.getMsgInput)

    '''thread creation'''
    tread = threading.Thread(target=chat.recvMsg, args=(clientSocket, saddr), daemon=True)
    treadFile = threading.Thread(target=chat.recvFile, daemon=True)
    tread.start()
    treadFile.start()

def gettime():
    curtime = str(time.ctime(time.time())).split(" ")
    return " ["+curtime[1]+" "+curtime[2]+" "+curtime[3][:-3]+"] "

def seticon(iconpath):
    iconsize = (40, 40)
    return PhotoImage(Image.open(iconpath).resize(iconsize, Image.NEAREST).convert("RGBA"))

class ChatRoom():
    def __init__(self, parent):
        global font_btn, font_content
        global clientName, msg_buf
        # window = top + middle + bottom
        self.top_frame = Frame(parent)
        self.middle_frame = Frame(parent)
        self.bottom_frame = Frame(parent)

        # icon
        iconsize = (40, 40)
        icon_slfile = PhotoImage(file="img/selectfile.png").subsample(30,30)

        # top: 顯示聊天訊息(listbox & scrollbar)
        self.scrollbar = Scrollbar(self.top_frame)
        self.listbox = Listbox(self.top_frame, yscrollcommand=self.scrollbar.set,
                               height=20, width=90, font=font_content, bg="#FFFFFF")
        self.scrollbar.config(command=self.listbox.yview)

        # middle: 選擇/儲存檔案
        self.txt_temp = Label(self.middle_frame, text="middle")
        self.txt_temp2 = Label(self.middle_frame, text="middle")
        self.button_slfile = Button(self.middle_frame, image=icon_slfile, borderwidth=0,
                                    command=self.browsefile)
        self.button_slfile.image = icon_slfile

        # bottom: 傳送聊天訊息或登出
        cN=clientName.get()
        cNlen=len(cN)
        if(cNlen>8):
            cN=cN[:8]+"..."
        self.txt_sendbox = Label(self.bottom_frame, text=cN + ":", font=font_content)
        self.entry_sendbox = Entry(self.bottom_frame, width=60, font=font_content, textvariable=input_msg)
        self.button_sendbox = Button(self.bottom_frame, text="Send", width=8, fg="#FFFFFF", bg="#5555CC", font=font_btn,
                                     command=self.getMsgInput)
        self.button_logout = Button(self.bottom_frame, text="Logout", width=8, fg="#FFFFFF", bg="#AAAAAA", font=font_btn,
                                     command=self.logout)

        # connect TCP Server
        self.file_srv_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpConnect()
        
        # pack widgets
        self.packUI()

    def tcpConnect(self):
        self.file_srv_skt.connect(taddr)
        self.file_srv_skt.send(clientName.get().encode('utf-8'))

    def packUI(self):
        # frame
        self.top_frame.pack(side=TOP,pady=10)
        self.middle_frame.pack(side=TOP,pady=10)
        self.bottom_frame.pack(side=BOTTOM,pady=10)

        # top
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.listbox.pack(side=LEFT, fill=BOTH, pady=5)

        # middle
        self.button_slfile.pack(side=BOTTOM,padx=2)

        # bottom
        self.txt_sendbox.pack(side=LEFT)
        self.entry_sendbox.pack(side=LEFT, padx=2)
        self.button_sendbox.pack(side=LEFT, padx=2)
        self.button_logout.pack(side=RIGHT, padx=2)

    def getMsgInput(self, event=None):
        global saddr
        global clientSocket
        global msg_buf, input_msg

        text = input_msg.get()

        if (text != ""):
            clientSocket.sendto(text.encode('utf-8'), saddr)
            self.entry_sendbox.delete(0,"end")
        else:
            pass

    def recvMsg(self, sock, addr):
        global clientName
        global msg_buf, listitemcounter, currenttime
        # 一個UDP連線在接收訊息前必須要讓系統知道所佔埠->需要先send一次
        sock.sendto(clientName.get().encode("utf-8"), addr)

        while (1):
            msg = sock.recv(1024)
            if (msg != ""):
                if (not currenttime or currenttime != gettime()):
                    currenttime = gettime()
                    self.listbox.insert(END,currenttime)
                    self.listbox.itemconfig(listitemcounter, {"fg": "#AAAAAA"})
                    listitemcounter += 1
                msg=msg.decode("utf-8")
                msg_buf.append(msg)
                if(len(msg) > 100):
                    tmp = msg.split("\n")
                    for i, s in enumerate(tmp):
                        self.listbox.insert(END, s)
                        if i == 0:
                            self.listbox.itemconfig(listitemcounter, {"fg": "#0000CC"})
                        else:
                            self.listbox.itemconfig(listitemcounter, {"fg": "#FF338A"})
                        listitemcounter += 1
                else:
                    self.listbox.insert(END,msg)
                if (msg[:21] == "<System notification>"):
                    self.listbox.itemconfig(listitemcounter, {"fg": "#0000CC"})
                listitemcounter += 1
                self.listbox.see(END)

    def recvFile(self):
        global listitemcounter, currenttime
        while True:
            name = self.file_srv_skt.recv(10)
            if(name != ""):
                name = name.decode().split("\0")[0]
                filename_msg = self.file_srv_skt.recv(100).decode()
                if(filename_msg != ""):
                    filename = filename_msg.split()[0]
                    print("File:", filename)
                    f = open(filename, 'wb')

                    filesize_msg = self.file_srv_skt.recv(10).decode()
                    if(filesize_msg != ""):
                        filesize = int(filesize_msg)
                        print("Size:", filesize)

                    if(filesize > 1024):
                        while filesize > 0:
                            print(filesize)
                            indata = self.file_srv_skt.recv(1024)
                            filesize -= 1024
                            f.write(indata)
                    else:
                        indata = self.file_srv_skt.recv(1024)
                        f.write(indata)
                    print("tetetetstet")
                    f.close()
                    msg = name + ": transfer file is [" + filename +"]"
                    print(msg)
                    if (not currenttime or currenttime != gettime()):
                        currenttime = gettime()
                        self.listbox.insert(END,currenttime)
                        self.listbox.itemconfig(listitemcounter, {"fg": "#AAAAAA"})
                        listitemcounter += 1
                    self.listbox.insert(END, msg)
                    self.listbox.itemconfig(listitemcounter, {"fg": "#B833FF"})
                    listitemcounter += 1
                    self.listbox.see(END)

    def browsefile(self):
        # get file path and name (return empty tuple if not select)
        filename = askopenfilename(filetypes=[("image", ".jpg"), ("image", ".png")])
        if(filename == ()):
            return
        self.sendFile(filename)
        
    def sendFile(self, filepath):
        # filename (max string size is 100)
        filename = filepath[::-1].split("/")[0][::-1] # complete path -> only filename
        filename_msg = filename +" "+ (99-len(filename))*'\0'
        self.file_srv_skt.send(filename_msg.encode('utf-8'))
        print("File: " + filename_msg)

        # filesize (max string size is 10)
        f = open(filepath, "rb")
        buf = f.read() # data type: bytes
        file_size = len(buf)
        file_size_msg = "0"*(10-len(str(file_size))) + str(file_size)
        self.file_srv_skt.send(file_size_msg.encode('utf-8'))
        print("Size: " + file_size_msg)

        # file data
        self.file_srv_skt.send(buf)

    def logout(self):
        global window
        global clientName, clientSocket
        '''send termination signal'''
        clientSocket.sendto("LOGOUTSIGNAL".encode('utf-8'), saddr)
        self.file_srv_skt.send("LOGOUTSIGNAL".encode('utf-8'))

        '''unpack chatting room widgets'''
        self.top_frame.pack_forget()
        self.middle_frame.pack_forget()
        self.bottom_frame.pack_forget()
        clientSocket.close()
        self.file_srv_skt.close()

        '''pack logout widgets'''
        txt_logout.config(text="Logout successfully.\n\nGoodbye, "+clientName.get()+"!")
        txt_logout.pack(side=TOP, pady=15)
        window.geometry("400x100")






#######################################################################################

# label / button########################################################################
##font
font_btn = tkfont(family="微軟正黑體", size=10, weight=BOLD)
font_content = tkfont(family="微軟正黑體", size=10)
font_cr = tkfont(family="Times", size=8, slant=ITALIC)
##login/logout phase
txt_getName = Label(window, text="Please enter your name", font=font_content)
entry_getName = Entry(window, width=30, font=font_content, textvariable=clientName)
button_getName = Button(window, text="Login!", width=8, fg="#FFFFFF", bg="#5555CC", font=font_btn,
                        command=client_online)
txt_logout=Label(window, text="", font=font_content)
##copyright
txt_copyright = Label(window, text="® SophieXin & KaielHsu 2021", font=font_cr)
#######################################################################################

# pack / place##########################################################################
##login
txt_getName.pack(side=TOP, pady=15)
entry_getName.pack(side=TOP, pady=5)
button_getName.pack(side=TOP, pady=10)
window.bind("<Return>", client_online)
##copyright
txt_copyright.pack(side=BOTTOM)
#######################################################################################

# window looping########################################################################
if __name__ == '__main__':
    window.mainloop()
