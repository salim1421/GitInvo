from tkinter import ttk
from employee import connect_database
from tkinter import *
from tkinter import messagebox


def add_category(catid, name, desc):
    if (
        catid == ""
        or name == ""
        or desc.strip() == ""
    ):
        messagebox.showerror("Error", "All Fields Are Required!")
        return

    try:
        conn, cursor = connect_database()
        if not conn or not cursor:
            return
        
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS category_data(
                catid INTEGER PRIMARY KEY,
                name VARCHAR(50),
                description VARCHAR(15)
            )
        '''
        )

        cursor.execute(
            """
            INSERT INTO category_data (catid, name, description)
            VALUES (%s, %s, %s)
            """,
            (catid, name, desc),
        )

        conn.commit()
        treeview_data()
        messagebox.showinfo("Success", "Employee added successfully")

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

    finally:
        cursor.close()
        conn.close()


def update_data(catid, name, desc):
    conn, cursor = connect_database()
    if not conn:
        return False

    try:
        cursor.execute(
            """
            UPDATE category_data
            SET name = %s,
            description = %s
            WHERE catid = %s
        """,
            (name, desc, catid),
        )

        if cursor.rowcount == 0:
            return False  # No record updated

        conn.commit()
        return True

    except Exception as e:
        print("Update Error:", e)
        return False

    finally:
        cursor.close()
        conn.close()


def delete_employee(catid):
    conn, cursor = connect_database()
    if not conn:
        return False

    try:
        cursor.execute("DELETE FROM category_data WHERE catid = %s", (int(catid),))

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
    cat_id_entry,
    cat_name_entry,
    cat_desc_entry,
):

    selected = event.widget.focus()
    if not selected:
        return

    row = event.widget.item(selected, "values")
    if not row:
        return

    clear_fields(
        cat_id_entry,
        cat_name_entry,
        cat_desc_entry,
        False,
    )

    cat_id_entry.insert(0, row[0])
    cat_name_entry.insert(0, row[1])
    cat_desc_entry.insert(0, row[2])


def clear_fields(
    cat_id_entry,
    cat_name_entry,
    cat_desc_entry,
    check,
):
    cat_id_entry.delete(0, END)
    cat_name_entry.delete(0, END)
    cat_desc_entry.delete(0, END)
    if check:
        cat_treeview.delete(*cat_treeview.get_children())


def treeview_data():
    conn, cursor = connect_database()
    if not conn:
        return
    try:
        cursor.execute(
            'SELECT * FROM category_data ORDER BY catid'
        )
        records = cursor.fetchall()
        cat_treeview.delete(*cat_treeview.get_children())
        for record in records:
            cat_treeview.insert('', END, values=record)
    except Exception as e:
        print(f'Cannot show treeview, due to {e}')
    finally:
        cursor.close()
        conn.close()
        

def fetch_data(cat_treeview):
    conn, cursor = connect_database()
    if not conn:
        return

    try:
        cursor.execute("""
            SELECT catid, name, description
            FROM category_data
            ORDER BY catid
        """)
        rows = cursor.fetchall()

        # Clear existing rows
        cat_treeview.delete(*cat_treeview.get_children())

        # Insert fresh data
        for row in rows:
            cat_treeview.insert("", END, values=row)

    except Exception as e:
        print("Fetch Error:", e)

    finally:
        cursor.close()
        conn.close()
    
    

def live_search_employee(name):
    conn, cursor = connect_database()
    if not conn:
        return []

    try:
        cursor.execute("""
            SELECT catid, name, description
            FROM category_data
            WHERE CAST(name AS TEXT) ILIKE %s
            ORDER BY catid
        """, (f"%{name}%",))
        
        return cursor.fetchall()

    except Exception as e:
        print("Live Search Error:", e)
        return []

    finally:
        cursor.close()
        conn.close()


def live_search_controller(keyword, cat_treeview):
    if keyword.strip() == "":
        cat_treeview.delete(*cat_treeview.get_children())
        for row in get_all_employees():
            cat_treeview.insert("", "end", values=row)
        return

    results = live_search_employee(keyword)

    cat_treeview.delete(*cat_treeview.get_children())

    for row in results:
        cat_treeview.insert("", "end", values=row)


def get_all_employees():
    conn, cursor = connect_database()
    if not conn:
        return []

    try:
        cursor.execute(
            """
            SELECT catid, name, description
            FROM category_data
            ORDER BY catid
        """
        )
        return cursor.fetchall()

    except Exception as e:
        print("Fetch Error:", e)
        return []

    finally:
        cursor.close()
        conn.close()


def show_all_controller(cat_treeview):
    cat_treeview.delete(*cat_treeview.get_children())

    for row in get_all_employees():
        cat_treeview.insert("", "end", values=row)



def category_form(window):
    global cat_treeview
    
    cat_frame = Frame(window, width=987, height=583)
    cat_frame.place(x=283, y=100)
    
    title_label = Label(cat_frame, text='Manage Supplier Details', font=('times new roman', 15, 'bold'), bg='#A1A1A1')
    title_label.place(x=0, y=0, relwidth=1)
    
    back = Button(
        cat_frame, text='Home', font=('times new roman', 10, 'bold'), fg='white', bg='navy', command=cat_frame.place_forget
    )
    back.place(x=0, y=0)
    
    header = Label(cat_frame, text='CATEGORIES', font=('times new roman', 30, 'bold'), pady=20)
    header.place(x=10, y=30)
    
    #Supplier Form
    cat_form_frame = Frame(cat_frame, width=400)
    cat_form_frame.place(x=20, y=120)
    
    cat_id_label = Label(cat_form_frame, text='S/No.', font=('times new roman', 12))
    cat_id_label.grid(row=0, column=0, pady=10)
    
    cat_id_entry = Entry(cat_form_frame, bg='lightblue')
    cat_id_entry.grid(row=0, column=1, pady=10)
    
    cat_name_label = Label(cat_form_frame, text='Name', font=('times new roman', 12))
    cat_name_label.grid(row=1, column=0, pady=10)
    
    cat_name_entry = Entry(cat_form_frame, bg='lightblue')
    cat_name_entry.grid(row=1, column=1, pady=10)
    
    cat_desc_label = Label(cat_form_frame, text='Description', font=('times new roman', 12))
    cat_desc_label.grid(row=2, column=0, pady=10)
    
    cat_desc_entry = Entry(cat_form_frame, bg='lightblue')
    cat_desc_entry.grid(row=2, column=1, pady=10)
    
    #CRUD buttons
    
    button_frame = Frame(cat_frame)
    button_frame.place(x=0, y=260)
    
    add_button = Button(
        button_frame, text='Add', font=('times new roman', 15, 'bold'), fg='white', bg='green',
        command=lambda:add_category(
            cat_id_entry.get(),
            cat_name_entry.get(),
            cat_desc_entry.get()
        )
    )
    add_button.grid(row=0, column=0, padx=5)
    
    
    # Update and functionalities
    def update_and_refresh():
        success = update_data(
            cat_id_entry.get(),
            cat_name_entry.get(),
            cat_desc_entry.get()
        )
        if success:
            fetch_data(cat_treeview)
            clear_fields(
                cat_id_entry,
                cat_name_entry,
                cat_desc_entry,
                False
            )
            messagebox.showinfo('Success', 'Data Update Successfully')
        else:
            messagebox.showerror('Error', 'Data Update Failed')
            
    update_button = Button(
        button_frame, text='Update', font=('times new roman', 15, 'bold'), fg='white', bg='navy',
        command=lambda:update_data(
            cat_id_entry.get(),
            cat_name_entry.get(),
            cat_desc_entry.get()
        )
    )
    update_button.config(command=update_and_refresh)
    update_button.grid(row=0, column=1, padx=5)

    clear_button = Button(
        button_frame, text='Clear', font=('times new roman', 15, 'bold'), fg='white', bg='gray',
        command=lambda:clear_fields(
            cat_id_entry,
            cat_name_entry,
            cat_desc_entry,
            False
        )
    )
    clear_button.grid(row=0, column=2, padx=5)

    #Delete and functionalities
    def delete_and_refresh():
        catid = cat_id_entry.get()

        if not catid:
            messagebox.showwarning("Warning", "Please select an employee to delete")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this employee?\nThis action cannot be undone.",
        )

        if not confirm:
            return

        success = delete_employee(catid)

        if success:
            fetch_data(cat_treeview)
            clear_fields(
                cat_id_entry,
                cat_name_entry,
                cat_desc_entry,
                False
            )
            messagebox.showinfo("Deleted", "Employee deleted successfully")
        else:
            messagebox.showerror("Error", "Delete failed or employee not found")
            
    delete_button = Button(
        button_frame, text='Delete', font=('times new roman', 15, 'bold'), fg='white', bg='red4',
    )
    delete_button.config(command=delete_and_refresh)
    delete_button.grid(row=0, column=3)
    
    
    #Supplier list
    
    search_frame = Frame(cat_frame)
    search_frame.place(x=500, y=50)
    
    
    search_label = Label(search_frame, text='Search', font=('times new roman', 11, 'bold'))
    search_label.grid(row=0, column=0)
    
    search_by_txt = StringVar()
    
    search_entry = Entry(search_frame, bg='lightblue', textvariable=search_by_txt)
    search_entry.grid(row=0, column=1, padx=15)
    
    show_all_button = Button(
        search_frame, text='Show All', font=('times new roman', 12, 'bold'), fg='white', bg='navy', command=lambda:show_all_controller(cat_treeview)
    )
    show_all_button.grid(row=0, column=2)
    
    #supplier treeview
    table_frame = Frame(cat_frame)
    table_frame.place(x=330, y=90, height=400)
    
    horizontal_scroll = Scrollbar(table_frame, orient=HORIZONTAL)
    vertical_scroll = Scrollbar(table_frame, orient=VERTICAL)
    
    cat_treeview = ttk.Treeview(
        table_frame, show='headings', columns=('S/No.', 'Name', 'Description'), xscrollcommand=horizontal_scroll.set,
        yscrollcommand=vertical_scroll.set
    )
    horizontal_scroll.config(command=cat_treeview.xview)
    vertical_scroll.config(command=cat_treeview.yview)
    horizontal_scroll.pack(fill=X, side=BOTTOM)
    vertical_scroll.pack(fill=Y, side=RIGHT)
    cat_treeview.pack(fill=BOTH, expand=True)
    
    cat_treeview.heading('S/No.', text='S/No.')
    cat_treeview.heading('Name', text='Name')
    cat_treeview.heading('Description', text='Description')
    
    treeview_data()
    
    #bindings
    cat_treeview.bind(
        "<ButtonRelease-1>",
        lambda event: select_data(
            event,
            cat_id_entry,
            cat_name_entry,
            cat_desc_entry,
        ),
    )
    search_entry.bind(
        "<KeyRelease>",
        lambda event: live_search_controller(
            search_by_txt.get(), cat_treeview
        ),
    )

    return cat_frame
    
    