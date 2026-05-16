from tkinter import *
from login import login_ui
from license import is_activated, activate
from tkinter import messagebox
from config import resource_path


import os

# window = Tk()
# window.geometry('1270x900+0+0')
# window.title('TkComms Records')
# 
# login_ui(window)
# window.mainloop()
# main.py


def show_activation_screen():

    path = os.path.normpath(resource_path("images/invo.ico"))
    print("Exists:", os.path.exists(path))  # must print True
    print("Size:", os.path.getsize(path))   # must be > 0

    win = Tk()
    win.title("Activate GitInvo")
    win.geometry("420x220")
    win.resizable(False, False)
    #win.iconbitmap(os.path.normpath(resource_path("images/invo.ico")))


    Label(win, text="GitInvo — License Activation",
          font=("Times New Roman", 16, "bold")).pack(pady=20)

    Label(win, text="Enter your license key:",
          font=("Times New Roman", 12)).pack()

    key_entry = Entry(win, width=35, font=("Times New Roman", 12), justify="center")
    key_entry.pack(pady=10)
    key_entry.insert(0, "GITINVO-XXXX-XXXX-XXXX")

    def try_activate():
        key = key_entry.get().strip()
        success, msg = activate(key)
        if success:
            messagebox.showinfo("Activated", msg, parent=win)
            win.destroy()
            launch_app()   # ← proceed to login
        else:
            messagebox.showerror("Failed", msg, parent=win)

    Button(win, text="Activate", font=("Times New Roman", 12, "bold"),
           bg="#0D3B19", fg="white", width=15,
           command=try_activate).pack(pady=10)

    win.mainloop()


def launch_app():
    
    window = Tk()                          # ← create main window here
    window.title("GitInvo")
    window.geometry("1270x700")
    window.resizable(False, False)
    
    icon = PhotoImage(file=os.path.normpath(resource_path("images/my_logo.png")))
    window.iconphoto(True, icon)
    
    login_ui(window)                       # ← pass window in
    window.mainloop()
    

if __name__ == "__main__":
    if is_activated():
        launch_app()        # ← already activated, go straight to login
    else:
        show_activation_screen()   # ← first run, ask for key
