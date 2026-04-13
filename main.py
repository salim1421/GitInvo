from tkinter import *
from login import login_ui
import bcrypt
from employee import connect_database


window = Tk()
window.geometry('1270x900+0+0')
window.title('TkComms Records')

login_ui(window)
window.mainloop()