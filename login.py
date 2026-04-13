from tkinter import *
from database import connect_database
from tkinter import messagebox
from dashboard import main_dashboard
import bcrypt # type: ignore
from sales import sales_form




def login_ui(window):

    def login_form():
        username = user_name_entry.get().strip()
        password = user_password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Enter username and password")
            return

        conn, cursor = connect_database()
        cursor.execute(
            "SELECT password, name, user_type FROM employee_data WHERE LOWER(name)=LOWER(?)",
            (username,)
        )
        result = cursor.fetchone()

        if result:
            db_password, full_name, user_type = result

            # bcrypt needs bytes
            if bcrypt.checkpw(password.encode('utf-8'), bytes(db_password)):

                if user_type == "Admin":
                    main_dashboard(window, full_name, user_type)
                    messagebox.showinfo('Success', f'Welcome Aboard, Mr {full_name}')
                else:
                    sales_form(window, cashier_name=full_name)

            else:
                messagebox.showerror("Login Failed", "Wrong password")
        else:
            messagebox.showerror("Login Failed", "Username not found")

        cursor.close()
        conn.close()


    def toggle_password():
        if user_password_entry.cget('show') == '*':
            user_password_entry.config(show='')
            toggle_btn.config(text='Hide')
        else:
            user_password_entry.config(show='*')
            toggle_btn.config(text='Show')


    main_frame = Frame(window, height=1270, width=1270, bg="#B3B1B1")
    main_frame.place(x=0, y=0)

    login_frame = Frame(main_frame, width=500, height=600)
    login_frame.place(x=450, y=50)

    window.l_image = PhotoImage(file='images/my_logo.png')

    login_image = Label(login_frame, image=window.l_image)
    login_image.pack(fill=X, padx=30, pady=30)

    login_label = Label(login_frame, text='My Inventory System', font=('times new roman', 20, 'bold'))
    login_label.pack(fill=X, pady=10)

    user_name_label = Label(login_frame, text='Enter Username:', font=('times new roman', 12, 'bold'))
    user_name_label.pack()

    user_name_entry = Entry(login_frame, width=50)
    user_name_entry.pack(pady=10)

    user_password_label = Label(login_frame, text='Password:', font=('times new roman', 12, 'bold'))
    user_password_label.pack()

    user_password_entry = Entry(login_frame, width=50, show='*')
    user_password_entry.pack(pady=10)

    login_button = Button(
        login_frame, text='Log In', font=('times new roman', 15, 'bold'), bg='navy', fg='white', width=20,
        command=lambda:login_form()
    )
    login_button.pack(pady=10)


    toggle_btn = Button(login_frame,
                        text='Show',
                        command=toggle_password)
    toggle_btn.pack(side=TOP, pady=5)


