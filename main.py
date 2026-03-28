from tkinter import *
from login import login_ui
import bcrypt
from employee import connect_database


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def create_default_user():
    conn, cursor = connect_database()
    if not conn:
        return

    try:
        cursor.execute("SELECT COUNT(*) FROM employee_data")
        user_count = cursor.fetchone()[0]

        if user_count == 0:
            # No users exist → create default admin
            default_id = 1
            default_username = "admin"
            default_user_type = 'Admin'
            default_password = hash_password("admin")  # IMPORTANT

            cursor.execute("""
                INSERT INTO employee_data (empid, name, user_type, password)
                VALUES (%s,%s, %s, %s)
            """, (default_id, default_username, default_user_type, default_password))

            conn.commit()

    finally:
        conn.close()


window = Tk()
window.geometry('1270x900+0+0')
window.title('TkComms Records')

create_default_user()
login_ui(window)
window.mainloop()