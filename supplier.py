from tkinter import ttk
from employee import connect_database
from tkinter import *
from tkinter import messagebox


def add_supplier(invoice_no, name, phone_no):
    if (
        invoice_no == ""
        or name == ""
        or phone_no == ""
    ):
        messagebox.showerror("Error", "All Fields Are Required!")
        return

    try:
        conn, cursor = connect_database()
        if not conn or not cursor:
            return
        
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS supplier_data(
                invoice_no INTEGER PRIMARY KEY,
                name VARCHAR(50),
                phone_no VARCHAR(15)
            )
        '''
        )

        cursor.execute(
            """
            INSERT INTO supplier_data (invoice_no, name, phone_no)
            VALUES (%s, %s, %s)
            """,
            (invoice_no, name, phone_no),
        )

        conn.commit()
        treeview_data()
        messagebox.showinfo("Success", "Employee added successfully")

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

    finally:
        cursor.close()
        conn.close()


def update_data(invoice_no, name, phone_no):
    conn, cursor = connect_database()
    if not conn:
        return False

    try:
        cursor.execute(
            """
            UPDATE supplier_data
            SET name = %s,
            phone_no = %s
            WHERE invoice_no = %s
        """,
            (name, phone_no, invoice_no),
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


def delete_employee(invoice_no):
    conn, cursor = connect_database()
    if not conn:
        return False

    try:
        cursor.execute("DELETE FROM supplier_data WHERE invoice_no = %s", (int(invoice_no),))

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
    invoice_no_entry,
    sup_name_entry,
    sup_phone_entry,
):

    selected = event.widget.focus()
    if not selected:
        return

    row = event.widget.item(selected, "values")
    if not row:
        return

    clear_fields(
        invoice_no_entry,
        sup_name_entry,
        sup_phone_entry,
        False,
    )

    invoice_no_entry.insert(0, row[0])
    sup_name_entry.insert(0, row[1])
    sup_phone_entry.insert(0, row[2])


def clear_fields(
    invoice_no_entry,
    sup_name_entry,
    sup_phone_entry,
    check,
):
    invoice_no_entry.delete(0, END)
    sup_name_entry.delete(0, END)
    sup_phone_entry.delete(0, END)
    if check:
        sup_treeview.delete(*sup_treeview.get_children())


def treeview_data():
    conn, cursor = connect_database()
    if not conn:
        return
    try:
        cursor.execute(
            'SELECT * FROM supplier_data ORDER BY invoice_no'
        )
        records = cursor.fetchall()
        sup_treeview.delete(*sup_treeview.get_children())
        for record in records:
            sup_treeview.insert('', END, values=record)
    except Exception as e:
        print(f'Cannot show treeview, due to {e}')
    finally:
        cursor.close()
        conn.close()
        

def fetch_data(sup_treeview):
    conn, cursor = connect_database()
    if not conn:
        return

    try:
        cursor.execute("""
            SELECT invoice_no, name, phone_no
            FROM supplier_data
            ORDER BY invoice_no
        """)
        rows = cursor.fetchall()

        # Clear existing rows
        sup_treeview.delete(*sup_treeview.get_children())

        # Insert fresh data
        for row in rows:
            sup_treeview.insert("", END, values=row)

    except Exception as e:
        print("Fetch Error:", e)

    finally:
        cursor.close()
        conn.close()
    
    

def live_search_suppliers(invoice_no):
    conn, cursor = connect_database()
    if not conn:
        return []

    try:
        cursor.execute("""
            SELECT invoice_no, name, phone_no
            FROM supplier_data
            WHERE CAST(invoice_no AS TEXT) ILIKE %s
            ORDER BY invoice_no
        """, (f"%{invoice_no}%",))
        
        return cursor.fetchall()

    except Exception as e:
        print("Live Search Error:", e)
        return []

    finally:
        cursor.close()
        conn.close()


def live_search_controller(keyword, sup_treeview):
    # If no search type selected → show all
    if keyword.strip() == "":
        sup_treeview.delete(*sup_treeview.get_children())
        for row in get_all_suppliers():
            sup_treeview.insert("", "end", values=row)
        return

    results = live_search_suppliers(keyword)

    sup_treeview.delete(*sup_treeview.get_children())

    for row in results:
        sup_treeview.insert("", "end", values=row)


def get_all_suppliers():
    conn, cursor = connect_database()
    if not conn:
        return []

    try:
        cursor.execute(
            """
            SELECT invoice_no, name, phone_no
            FROM supplier_data
            ORDER BY invoice_no
        """
        )
        return cursor.fetchall()

    except Exception as e:
        print("Fetch Error:", e)
        return []

    finally:
        cursor.close()
        conn.close()


def show_all_controller(sup_treeview):
    sup_treeview.delete(*sup_treeview.get_children())

    for row in get_all_suppliers():
        sup_treeview.insert("", "end", values=row)



def supplier_form(window):
    global sup_treeview
    
    sup_frame = Frame(window, width=987, height=583)
    sup_frame.place(x=283, y=100)
    
    title_label = Label(sup_frame, text='Manage Supplier Details', font=('times new roman', 15, 'bold'), bg='#A1A1A1')
    title_label.place(x=0, y=0, relwidth=1)
    
    back = Button(
        sup_frame, text='Home', font=('times new roman', 10, 'bold'), fg='white', bg='navy', command=sup_frame.place_forget
    )
    back.place(x=0, y=0)
    
    header = Label(sup_frame, text='My Suppliers', font=('times new roman', 30, 'bold'), pady=20)
    header.place(x=10, y=30)
    
    #Supplier Form
    sup_form_frame = Frame(sup_frame, width=400)
    sup_form_frame.place(x=20, y=120)
    
    invoice_no_label = Label(sup_form_frame, text='Invoice No.', font=('times new roman', 12))
    invoice_no_label.grid(row=0, column=0, pady=10)
    
    invoice_no_entry = Entry(sup_form_frame, bg='lightblue')
    invoice_no_entry.grid(row=0, column=1, pady=10)
    
    sup_name_label = Label(sup_form_frame, text='Name', font=('times new roman', 12))
    sup_name_label.grid(row=1, column=0, pady=10)
    
    sup_name_entry = Entry(sup_form_frame, bg='lightblue')
    sup_name_entry.grid(row=1, column=1, pady=10)
    
    sup_phone_label = Label(sup_form_frame, text='Phone Number', font=('times new roman', 12))
    sup_phone_label.grid(row=2, column=0, pady=10)
    
    sup_phone_entry = Entry(sup_form_frame, bg='lightblue')
    sup_phone_entry.grid(row=2, column=1, pady=10)
    
    #CRUD buttons
    
    button_frame = Frame(sup_frame)
    button_frame.place(x=0, y=260)
    
    add_button = Button(
        button_frame, text='Add', font=('times new roman', 15, 'bold'), fg='white', bg='green',
        command=lambda:add_supplier(
            invoice_no_entry.get(),
            sup_name_entry.get(),
            sup_phone_entry.get()
        )
    )
    add_button.grid(row=0, column=0, padx=5)
    
    
    # Update and functionalities
    def update_and_refresh():
        success = update_data(
            invoice_no_entry.get(),
            sup_name_entry.get(),
            sup_phone_entry.get()
        )
        if success:
            fetch_data(sup_treeview)
            clear_fields(
                invoice_no_entry,
                sup_name_entry,
                sup_phone_entry,
                False
            )
            messagebox.showinfo('Success', 'Data Update Successfully')
        else:
            messagebox.showerror('Error', 'Data Update Failed')
            
    update_button = Button(
        button_frame, text='Update', font=('times new roman', 15, 'bold'), fg='white', bg='navy',
        command=lambda:update_data(
            invoice_no_entry.get(),
            sup_name_entry.get(),
            sup_phone_entry.get()
        )
    )
    update_button.config(command=update_and_refresh)
    update_button.grid(row=0, column=1, padx=5)

    clear_button = Button(
        button_frame, text='Clear', font=('times new roman', 15, 'bold'), fg='white', bg='gray',
        command=lambda:clear_fields(
            invoice_no_entry,
            sup_name_entry,
            sup_phone_entry,
            False
        )
    )
    clear_button.grid(row=0, column=2, padx=5)

    #Delete and functionalities
    def delete_and_refresh():
        invoice_no = invoice_no_entry.get()

        if not invoice_no:
            messagebox.showwarning("Warning", "Please select an employee to delete")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this employee?\nThis action cannot be undone.",
        )

        if not confirm:
            return

        success = delete_employee(invoice_no)

        if success:
            fetch_data(sup_treeview)
            clear_fields(
                invoice_no_entry,
                sup_name_entry,
                sup_phone_entry,
                FALSE,
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
    
    search_frame = Frame(sup_frame)
    search_frame.place(x=500, y=50)
    
    
    search_label = Label(search_frame, text='Search', font=('times new roman', 11, 'bold'))
    search_label.grid(row=0, column=0)
    
    search_by_txt = StringVar()
    
    search_entry = Entry(search_frame, bg='lightblue', textvariable=search_by_txt)
    search_entry.grid(row=0, column=1, padx=15)
    
    show_all_button = Button(
        search_frame, text='Show All', font=('times new roman', 12, 'bold'), fg='white', bg='navy', command=lambda:show_all_controller(sup_treeview)
    )
    show_all_button.grid(row=0, column=2)
    
    #supplier treeview
    table_frame = Frame(sup_frame)
    table_frame.place(x=330, y=90, height=400)
    
    horizontal_scroll = Scrollbar(table_frame, orient=HORIZONTAL)
    vertical_scroll = Scrollbar(table_frame, orient=VERTICAL)
    
    sup_treeview = ttk.Treeview(
        table_frame, show='headings', columns=('Invoice No.', 'Name', 'Phone Number'), xscrollcommand=horizontal_scroll.set,
        yscrollcommand=vertical_scroll.set
    )
    horizontal_scroll.config(command=sup_treeview.xview)
    vertical_scroll.config(command=sup_treeview.yview)
    horizontal_scroll.pack(side=BOTTOM, fill=X)
    vertical_scroll.pack(side=RIGHT, fill=Y)
    sup_treeview.pack(fill=BOTH, expand=True)
    
    sup_treeview.heading('Invoice No.', text='Invoice No.')
    sup_treeview.heading('Name', text='Name')
    sup_treeview.heading('Phone Number', text='Phone Number')
    
    treeview_data()
    
    #bindings
    sup_treeview.bind(
        "<ButtonRelease-1>",
        lambda event: select_data(
            event,
            invoice_no_entry,
            sup_name_entry,
            sup_phone_entry,
        ),
    )
    search_entry.bind(
        "<KeyRelease>",
        lambda event: live_search_controller(
            search_by_txt.get(), sup_treeview
        ),
    )

    return sup_frame
    
    