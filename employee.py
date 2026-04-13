from tkinter import *
import psycopg2 # type: ignore
from tkinter import messagebox
from tkinter import ttk
from decouple import config # type: ignore
from database import connect_database
import bcrypt


def add_employee(name, phone_number, user_type, password):
    if (
        name == ""
        or phone_number == ""
        or user_type == ""
        or user_type == "Choose User Type"
        or password == ""
    ):
        messagebox.showerror("Error", "All Fields Are Required!")
        return

    try:
        conn, cursor = connect_database()
        if not conn or not cursor:
            return

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor.execute(
            """
            INSERT INTO employee_data (name, phone_number, user_type, password)
            VALUES (?, ?, ?, ?)
            """,
            (name, phone_number, user_type, hashed_password),
        )

        conn.commit()
        treeview_data()
        messagebox.showinfo("Success", "Employee added successfully")

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

    finally:
        cursor.close()
        conn.close()


def update_data(name, phone, user_type, password):
    conn, cursor = connect_database()
    if not conn:
        return False

    try:
        if password:  # only update password if entered
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

            cursor.execute(
                """
                UPDATE employee_data
                SET name=?, phone_number=?, user_type=?, password=?
                WHERE empid=?
                """,
                (name, phone, user_type, hashed_password),
            )
        else:
            cursor.execute(
                """
                UPDATE employee_data
                SET name=?, phone_number=?, user_type=?
                WHERE empid=?
                """,
                (name, phone, user_type),
            )

        if cursor.rowcount == 0:
            return False

        conn.commit()
        return True

    except Exception as e:
        print("Update Error:", e)
        return False

    finally:
        cursor.close()
        conn.close()


def delete_employee(empid):
    conn, cursor = connect_database()
    if not conn:
        return False

    try:
        cursor.execute("DELETE FROM employee_data WHERE empid = ?", (int(empid),))

        if cursor.rowcount == 0:
            return False

        conn.commit()
        return True

    except Exception as e:
        print("Delete Error:", e)
        return False

    finally:
        cursor.close()
        conn.close()


def select_data(
    event,
    empid,
    emp_name_entry,
    emp_phone_entry,
    emp_user_type,
    emp_password_entry,
):

    selected = event.widget.focus()
    if not selected:
        return

    row = event.widget.item(selected, "values")
    if not row:
        return

    clear_fields(
        emp_name_entry,
        emp_phone_entry,
        emp_user_type,
        emp_password_entry,
        False,
    )

    empid.set(row[0])
    emp_name_entry.insert(0, row[1])
    emp_phone_entry.insert(0, row[2])
    emp_user_type.set(row[3])

    # 🔐 NEVER load password from Treeview
    emp_password_entry.delete(0, END)


def clear_fields(
    emp_name_entry,
    emp_phone_entry,
    emp_user_type,
    emp_password_entry,
    check,
):
    emp_name_entry.delete(0, END)
    emp_phone_entry.delete(0, END)
    emp_user_type.set("Select User Type")
    emp_password_entry.delete(0, END)
    if check:
        emp_treeview.delete(*emp_treeview.get_children())


def treeview_data():
    conn, cursor = connect_database()
    if not conn:
        return
    try:
        cursor.execute(
            'SELECT * FROM employee_data ORDER BY empid'
        )
        records = cursor.fetchall()
        emp_treeview.delete(*emp_treeview.get_children())
        for record in records:
            emp_treeview.insert('', END, values=record)
    except Exception as e:
        print(f'Cannot show treeview, due to {e}')
    finally:
        cursor.close()
        conn.close()
        

def fetch_data(emp_treeview):
    conn, cursor = connect_database()
    if not conn:
        return

    try:
        cursor.execute("""
            SELECT empid, name, phone_number, user_type
            FROM employee_data
            ORDER BY empid
        """)
        rows = cursor.fetchall()

        # Clear existing rows
        emp_treeview.delete(*emp_treeview.get_children())

        # Insert fresh data
        for row in rows:
            emp_treeview.insert("", END, values=row)

    except Exception as e:
        print("Fetch Error:", e)

    finally:
        cursor.close()
        conn.close()
    
    

def live_search_employee(search_by, keyword):
    conn, cursor = connect_database()
    if not conn:
        return []

    try:
        query_map = {
            "Employee ID": "CAST(empid AS TEXT) LIKE ?",
            "Name": "name LIKE ?",
            "Phone": "phone_number LIKE ?",
        }

        sql = f"""
            SELECT empid, name, phone_number, user_type
            FROM employee_data
            WHERE {query_map[search_by]}
            ORDER BY empid
        """

        cursor.execute(sql, (f"%{keyword}%",))
        return cursor.fetchall()

    except Exception as e:
        print("Live Search Error:", e)
        return []

    finally:
        cursor.close()
        conn.close()


def live_search_controller(search_by, keyword, emp_treeview):
    # If no search type selected → show all
    if search_by == "Select" or keyword.strip() == "":
        emp_treeview.delete(*emp_treeview.get_children())
        for row in get_all_employees():
            emp_treeview.insert("", "end", values=row)
        return

    results = live_search_employee(search_by, keyword)

    emp_treeview.delete(*emp_treeview.get_children())

    for row in results:
        emp_treeview.insert("", "end", values=row)


def get_all_employees():
    conn, cursor = connect_database()
    if not conn:
        return []

    try:
        cursor.execute(
            """
            SELECT empid, name, phone_number, user_type
            FROM employee_data
            ORDER BY empid
        """
        )
        return cursor.fetchall()

    except Exception as e:
        print("Fetch Error:", e)
        return []

    finally:
        cursor.close()
        conn.close()


def show_all_controller(emp_treeview):
    emp_treeview.delete(*emp_treeview.get_children())

    for row in get_all_employees():
        emp_treeview.insert("", "end", values=row)


def employee_form(window):
    global emp_treeview
    conn, cursor = connect_database()
    if not conn:
        return

    emp_frame = Frame(window, height=890, width=987)
    emp_frame.place(x=283, y=100)

    title_label = Label(
        emp_frame,
        text="Manage Employee Details",
        font=("times new roman", 15, "bold"),
        bg="#A1A1A1",
    )
    title_label.place(x=0, y=0, relwidth=1)

    back = Button(
        emp_frame,
        text="Home",
        font=("times new roman", 10, "bold"),
        fg="white",
        bg="navy",
        command=emp_frame.place_forget,
    )
    back.place(x=0, y=0)

    search_frame = Frame(emp_frame)
    search_frame.place(x=200, y=50)

    search_txt_var = StringVar()
    search_by_var = StringVar(value='Select')
    empid = StringVar()

    search_by = ttk.Combobox(
        search_frame,
        values=("IDs", "Name", "Phone Number"),
        font=("times new roman", 12, "bold"),
        state="readonly",
        textvariable=search_by_var
    )
    search_by.set("Search By")
    search_by.grid(row=0, column=0, padx=10)

    search_entry = Entry(search_frame, bg="lightblue", textvariable=search_txt_var)
    search_entry.grid(row=0, column=1, padx=10)

    show_all_button = Button(
        search_frame,
        text="Show All",
        font=("times new roman", 12, "bold"),
        fg="white",
        bg="navy",
        command=lambda:show_all_controller(emp_treeview)
    )
    show_all_button.grid(row=0, column=2)

    # employee list
    
    table_frame = Frame(emp_frame)
    table_frame.place(x=100, y=100, height=200)
    horizontal_scroll = Scrollbar(table_frame, orient=HORIZONTAL)
    vertical_scroll = Scrollbar(table_frame, orient=VERTICAL)

    emp_treeview = ttk.Treeview(
        table_frame,
        columns=("Ids", "Name", "Phone Number", "User Type"),
        show="headings",
        xscrollcommand=horizontal_scroll.set,
        yscrollcommand=vertical_scroll.set
    )
    
    horizontal_scroll.config(command=emp_treeview.xview)
    vertical_scroll.config(command=emp_treeview.yview)
    horizontal_scroll.pack(side='bottom', fill=X)
    vertical_scroll.pack(side='right', fill=Y)

    emp_treeview.pack(fill=X, expand=True)

    emp_treeview.column("Ids", width=30)

    emp_treeview.heading("Ids", text="IDs")
    emp_treeview.heading("Name", text="Name")
    emp_treeview.heading("Phone Number", text="Phone Number")
    emp_treeview.heading("User Type", text="User Type")
    
    treeview_data()

    # employee Form
    emp_form_frame = Frame(emp_frame)
    emp_form_frame.place(x=50, y=330)

    emp_name_label = Label(emp_form_frame, text="Name", font=("times new roman", 12))
    emp_name_label.grid(row=0, column=2)

    emp_name_entry = Entry(emp_form_frame, bg="lightblue")
    emp_name_entry.grid(row=0, column=3, padx=5)

    emp_phone_label = Label(
        emp_form_frame, text="Phone Number", font=("times new roman", 12)
    )
    emp_phone_label.grid(row=0, column=4)

    emp_phone_entry = Entry(emp_form_frame, bg="lightblue")
    emp_phone_entry.grid(row=0, column=5, padx=5)

    emp_user_label = Label(
        emp_form_frame, text="User Type", font=("times new roman", 12)
    )
    emp_user_label.grid(row=1, column=2)

    emp_user_type = ttk.Combobox(
        emp_form_frame,
        values=("Admin", "Regular"),
        font=("times new roman", 12),
        state="readonly",
    )
    emp_user_type.set("Select User Type")
    emp_user_type.grid(row=1, column=3, padx=5)

    emp_password_label = Label(
        emp_form_frame, text="Password", font=("times new roman", 12)
    )
    emp_password_label.grid(row=1, column=4, padx=5)

    emp_password_entry = Entry(emp_form_frame, bg="lightblue")
    emp_password_entry.grid(row=1, column=5, padx=5)

    # CRUD buttons

    button_frame = Frame(emp_frame)
    button_frame.place(x=50, y=400)

    add_button = Button(
        button_frame,
        text="Add",
        font=("times new roman", 15, "bold"),
        fg="white",
        bg="green",
        width=15,
        command=lambda:add_employee(
            emp_name_entry.get(),
            emp_phone_entry.get(),
            emp_user_type.get(),
            emp_password_entry.get()
        )
    )
    add_button.grid(row=0, column=0, padx=5)

    # update and functionalities
    def update_and_refresh():
        success = update_data(
            emp_name_entry.get(),
            emp_phone_entry.get(),
            emp_user_type.get(),
            emp_password_entry.get(),
        )

        if success:
            fetch_data(emp_treeview)
            messagebox.showinfo("Success", "Employee updated")
        else:
            messagebox.showerror("Error", "Update failed")

    update_button = Button(
        button_frame,
        text="Update",
        font=("times new roman", 15, "bold"),
        fg="white",
        bg="navy",
        width=15,
        command=lambda: update_data(
            emp_name_entry.get(),
            emp_phone_entry.get(),
            emp_user_type.get(),
            emp_password_entry.get(),
        ),
    )
    update_button.config(command=update_and_refresh)
    update_button.grid(row=0, column=1, padx=5)

    clear_button = Button(
        button_frame,
        text="Clear",
        font=("times new roman", 15, "bold"),
        fg="white",
        bg="gray",
        width=15,
        command=lambda: clear_fields(
            emp_name_entry,
            emp_phone_entry,
            emp_user_type,
            emp_password_entry,
            FALSE,
        ),
    )
    clear_button.grid(row=0, column=2, padx=5)

    # delete and functionalities
    def delete_and_refresh(empid):
        if not empid.get():
            messagebox.showwarning("Warning", "Please select an employee to delete")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this employee?\nThis action cannot be undone.",
        )

        if not confirm:
            return

        success = delete_employee(empid.get())

        if success:
            fetch_data(emp_treeview)
            clear_fields(
                emp_name_entry,
                emp_phone_entry,
                emp_user_type,
                emp_password_entry,
                False,
            )
            messagebox.showinfo("Deleted", "Employee deleted successfully")
        else:
            messagebox.showerror("Error", "Delete failed or employee not found")

    delete_button = Button(
        button_frame,
        text="Delete",
        font=("times new roman", 15, "bold"),
        fg="white",
        bg="red4",
        width=15,
        command=lambda:delete_and_refresh(empid)
    )
    delete_button.grid(row=0, column=3)
    
    
    emp_treeview.bind(
        "<ButtonRelease-1>",
        lambda event: select_data(
            event,
            empid,
            emp_name_entry,
            emp_phone_entry,
            emp_user_type,
            emp_password_entry,
        ),
    )
    search_entry.bind(
        "<KeyRelease>",
        lambda event: live_search_controller(
            search_by_var.get(), search_txt_var.get(), emp_treeview
        ),
    )
    connect_database()
    return emp_frame