from tkinter import ttk
from employee import connect_database
from tkinter import *
from tkinter import messagebox


def get_category_and_supplier(prod_cat_entry, prod_sup_entry):
    category_option = []
    supplier_option = []
    
    conn, cursor = connect_database()
    if not conn or not cursor:
        return
    
    cursor.execute(
        'SELECT name FROM category_data'
    )
    names = cursor.fetchall()
    if len(names) > 0:
        prod_cat_entry.set('Select')
        for name in names:
            category_option.append(name[0])
        prod_cat_entry.config(values=category_option)
        
    cursor.execute(
        'SELECT name FROM supplier_data'
    )
    names = cursor.fetchall()
    if len(names) > 0:
        prod_sup_entry.set('Select')
        for name in names:
            supplier_option.append(name[0])
        prod_sup_entry.config(values=supplier_option)


def treeview_data(prod_treeview):
    conn, cursor = connect_database()
    if not conn:
        return
    try:
        cursor.execute(
            """SELECT id,
                name,
                unit_cost,
                detail,
                category,
                supplier,
                quantity,
                status
                FROM product_data
                ORDER BY id"""
        )
        data = cursor.fetchall()
        prod_treeview.delete(*prod_treeview.get_children())
        for datum in data:
            prod_treeview.insert('', END, values=datum)
    except Exception as e:
        print(f'Cannot show treeview due to, {e}')

        
def add_product(
    name, price, detail, category, supplier, quantity, status
    ):
    
    if category == 'Select':
        messagebox.showerror('Error', 'Please select a category')
        return
    elif supplier == 'Select':
        messagebox.showerror('Error', 'Please select a supplier')
        return
    elif (
        name == '' or price == '' or detail == '' or quantity == '' or status == 'Select'
    ):
        messagebox.showerror('Error', 'All Fields Are Required!')
        return
    
    try:
        conn, cursor = connect_database()
        if not conn or not cursor:
            return
        
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS product_data(
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name VARCHAR(50),
                unit_cost DECIMAL(10, 2),
                selling_price DECIMAL(10, 2),
                detail VARCHAR(50),
                category VARCHAR(20),
                supplier VARCHAR(50),
                quantity INT NOT NULL CHECK(quantity > 0),
                status VARCHAR(8),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

            )
        '''
        )
        cursor.execute('SELECT * FROM product_data WHERE name=%s AND category=%s AND supplier=%s', (name, category, supplier))
        existing_product = cursor.fetchone()
        if existing_product:
            messagebox.showerror('Error', 'Product Already Exists')
            return
        cursor.execute(
            '''
            INSERT INTO product_data(name, unit_cost, detail, category, supplier, quantity, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (name, price, detail, category, supplier, quantity, status)
        )
        
        conn.commit()
        treeview_data(prod_treeview)
        messagebox.showinfo('Success', 'Product Uploaded Successfully')
    except Exception as e:
        messagebox.showerror('Error', f'Error Due To {e}')
    finally:
        conn.close()
        cursor.close()
        
        
def update_data(
    prod_id,
    name,
    price,
    detail,
    category,
    supplier,
    quantity,
    status
):
    if not id or id == "":
        messagebox.showerror("Error", "Please select a product to update")
        return False
    
    conn, cursor = connect_database()
    if not conn:
        return
    
    try:
        cursor.execute(
            '''
            UPDATE product_data
            SET name = %s,
            unit_cost = %s,
            detail = %s,
            category = %s,
            supplier = %s,
            quantity = %s,
            status = %s
            WHERE id = %s
            ''', (name, price, detail, category, supplier, quantity, status, int(prod_id))
        )
        if cursor.rowcount == 0:
            return False
        
        conn.commit()
        return True
        treeview_data(prod_treeview)
    finally:
        conn.close()
        cursor.close()


def select_data(
    event,
    prod_id,
    prod_name_entry,
    prod_price_entry,
    prod_detail_entry,
    prod_cat_entry,
    prod_sup_entry,
    prod_quantity_entry,
    prod_status,
):
    selected = event.widget.focus()
    if not selected:
        return
    
    row = event.widget.item(selected, 'values')
    if not row:
        return
    
    clear_fields(
        prod_name_entry,
        prod_price_entry,
        prod_detail_entry,
        prod_cat_entry,
        prod_sup_entry,
        prod_quantity_entry,
        prod_status,
        False
    )
    prod_id.set(row[0])
    prod_name_entry.insert(0, row[1])
    prod_price_entry.insert(0, row[2])
    prod_detail_entry.insert(0, row[3])
    prod_cat_entry.set(row[4])
    prod_sup_entry.set(row[5])
    prod_quantity_entry.insert(0, row[6])
    prod_status.set(row[7])


def clear_fields(
    prod_name_entry,
    prod_price_entry,
    prod_detail_entry,
    prod_cat_entry,
    prod_sup_entry,
    prod_quantity_entry,
    prod_status,
    check
):
    prod_name_entry.delete(0, END)
    prod_price_entry.delete(0, END)
    prod_detail_entry.delete(0, END)
    prod_cat_entry.set('Select')
    prod_sup_entry.set('Select')
    prod_quantity_entry.delete(0, END)
    prod_status.set('Select')
    if check:
        prod_treeview.delete(*prod_treeview.get_children())
        
        
def delete_data(prod_id):
    conn, cursor = connect_database()
    if not conn:
        return
    try:
        cursor.execute(
            'DELETE FROM product_data WHERE id=%s', (prod_id.get(),)
        )
        if cursor.rowcount == 0:
            return False
        
        conn.commit()
        treeview_data(prod_treeview)
        prod_id.set('')
        return True
    finally:
        conn.close()
        cursor.close()
        

def get_all_products():
    conn, cursor = connect_database()
    if not conn:
        return []

    try:
        cursor.execute(
            """
            SELECT id, name, unit_cost, detail, category, supplier, quantity, status FROM product_data
            ORDER BY id
        """
        )
        return cursor.fetchall()

    except Exception as e:
        print("Fetch Error:", e)
        return []

    finally:
        cursor.close()
        conn.close()


def live_search_query(search_by, keyword):
    conn, cursor = connect_database()
    if not conn:
        return []

    try:
        query_map = {
            'Name': 'name',
            'Category': 'category',
            'Status': 'status'
        }

        column = query_map.get(search_by)
        if not column:
            return []

        sql = f"""
            SELECT id, name, unit_cost, detail, category, supplier, quantity, status
            FROM product_data
            WHERE {column} ILIKE %s
            ORDER BY id
        """

        cursor.execute(sql, (f"%{keyword}%",))
        return cursor.fetchall()

    except Exception as e:
        print(f'Cannot fetch live search data due to: {e}')
        return []

    finally:
        cursor.close()
        conn.close()

        

def live_search(search_by, keyword, prod_treeview):
    if search_by.strip() == "Search By" or keyword.strip() == '':
        prod_treeview.delete(*prod_treeview.get_children())
        for data in get_all_products():
            prod_treeview.insert('', END, values=data)
        return
    results = live_search_query(search_by, keyword)
    prod_treeview.delete(*prod_treeview.get_children())
    
    for result in results:
        prod_treeview.insert('', 'end', values=result)


def show_all_controller(prod_treeview):
    prod_treeview.delete(*prod_treeview.get_children())

    for row in get_all_products():
        prod_treeview.insert("", "end", values=row)


def product_form(window):
    global prod_treeview
    
    product_frame = Frame(window, width=987, height=583)
    product_frame.place(x=283, y=100)
    
    title_label = Label(product_frame, text='Manage Products Details', font=('times new roman', 15, 'bold'), bg='#A1A1A1')
    title_label.place(x=0, y=0, relwidth=1)
    
    back = Button(
        product_frame, text='Home', font=('times new roman', 10, 'bold'), fg='white', bg='navy', command=lambda:product_frame.place_forget()
    )
    back.place(x=0, y=0)
    
    #product CRUD
    
    left_frame = Frame(product_frame, width=350, bd=2, relief=RIDGE)
    left_frame.place(x=20, y=70)
    
    title = Label(product_frame, text='Manage Products', font=('times new roman', 15, 'bold'), fg='white', bg='navy')
    title.place(x=20, y=40, width=286)
    
    prod_id = StringVar()
    prod_id_entry = Entry(left_frame, textvariable=prod_id, state='readonly')
    prod_id_entry.grid_forget()

    prod_name_label = Label(left_frame, text='Name', font=('times new roman', 12, 'bold'))
    prod_name_label.grid(row=3, column=0, padx=10, pady=15)
    
    prod_name_entry = Entry(left_frame, bg='lightblue', width=25)
    prod_name_entry.grid(row=3, column=1, padx=10)
    
    prod_price_label = Label(left_frame, text='Price', font=('times new roman', 12, 'bold'))
    prod_price_label.grid(row=4, column=0, padx=10, pady=15)
    
    prod_price_entry = Entry(left_frame, bg='lightblue', width=25)
    prod_price_entry.grid(row=4, column=1, padx=10)

    prod_detail_label = Label(left_frame, text='Detail', font=('times new roman', 12, 'bold'))
    prod_detail_label.grid(row=5, column=0, padx=10, pady=15)
    
    prod_detail_entry = Entry(left_frame, bg='lightblue', width=25)
    prod_detail_entry.grid(row=5, column=1, padx=10)

    prod_cat_label = Label(left_frame, text='Category', font=('times new roman', 12, 'bold'))
    prod_cat_label.grid(row=6, column=0, padx=10, pady=15)
    
    prod_cat_entry = ttk.Combobox(left_frame, width=25, state='readonly')
    prod_cat_entry.set('Empty')
    prod_cat_entry.grid(row=6, column=1, padx=10)
    
    prod_sup_label = Label(left_frame, text='Supplier', font=('times new roman', 12, 'bold'))
    prod_sup_label.grid(row=7, column=0, padx=10, pady=15)
    
    prod_sup_entry = ttk.Combobox(left_frame, width=25, state='readonly')
    prod_sup_entry.set('Empty')
    prod_sup_entry.grid(row=7, column=1, padx=10)

    prod_quantity_label = Label(left_frame, text='Quantity', font=('times new roman', 12, 'bold'))
    prod_quantity_label.grid(row=8, column=0, padx=10, pady=15)
    
    prod_quantity_entry = Entry(left_frame, bg='lightblue', width=25)
    prod_quantity_entry.grid(row=8, column=1, padx=10)
    
    prod_status_label = Label(left_frame, text='Status', font=('times new roman', 12, 'bold'))
    prod_status_label.grid(row=9, column=0, padx=10, pady=15)
    
    prod_status = ttk.Combobox(left_frame, values=('Active', 'Not Active'), width=25, state='readonly')
    prod_status.set('Select')
    prod_status.grid(row=9, column=1, padx=10)

    #buttons
    
    button_frame = Frame(left_frame)
    button_frame.grid(row=10, columnspan=4, pady=10)
    
    add_button = Button(
        button_frame, text='Add', font=('times new roman', 12, 'bold'), bg='darkgreen', fg='white',
        command=lambda:add_product(
            prod_name_entry.get(),
            prod_price_entry.get(),
            prod_detail_entry.get(),
            prod_cat_entry.get(),
            prod_sup_entry.get(),
            prod_quantity_entry.get(),
            prod_status.get(),
        )
    )
    add_button.grid(row=0, column=0, padx=5)
    
    #update and functionalities
    def update_and_refresh():
        success = update_data(
            prod_id.get(),
            prod_name_entry.get(),
            prod_price_entry.get(),
            prod_detail_entry.get(),
            prod_cat_entry.get(),
            prod_sup_entry.get(),
            prod_quantity_entry.get(),
            prod_status.get()
        )
        if success:
            treeview_data(prod_treeview)
            messagebox.showinfo('Success', 'Product data updated successfully')
        else:
            messagebox.showerror('Error', 'Date Update Failed')
            
    
    update_button = Button(
        button_frame, text='Update', font=('times new roman', 12, 'bold'), bg='navy', fg='white',
        command=lambda:update_data(
            prod_id.get(),
            prod_name_entry.get(),
            prod_price_entry.get(),
            prod_detail_entry.get(),
            prod_cat_entry.get(),
            prod_sup_entry.get(),
            prod_quantity_entry.get(),
            prod_status.get()
        )
    )
    update_button.config(command=update_and_refresh)
    update_button.grid(row=0, column=1, padx=5)
    
    clear_button = Button(
        button_frame, text='Clear', font=('times new roman', 12, 'bold'), bg='gray', fg='white',
        command=lambda:clear_fields(
            prod_name_entry,
            prod_price_entry,
            prod_detail_entry,
            prod_cat_entry,
            prod_sup_entry,
            prod_quantity_entry,
            prod_status,
            False
        )
    )
    clear_button.grid(row=0, column=2, padx=7)
    
    #Delete and functionalities
    def delete_and_refresh():
        
        confirm = messagebox.askyesno(
            'Confirm Deletion',
            'Are you sure you want to delete data, This action cannot be undone.'
        )
        if not confirm:
            return        
        success = delete_data(prod_id)
        if success:
            treeview_data(prod_treeview)
            clear_fields(
                prod_name_entry,
                prod_price_entry,
                prod_detail_entry,
                prod_cat_entry,
                prod_sup_entry,
                prod_quantity_entry,
                prod_status,
                False
            )
            messagebox.showinfo('Success', 'Product Deleted Successfully')
        else:
            messagebox.showerror('Error', 'Data Deletion Failed')
        
    delete_button = Button(
        button_frame, text='Delete', font=('times new roman', 12, 'bold'), bg='red4', fg='white',
        command=lambda:delete_data(prod_id)
    )
    delete_button.config(command=delete_and_refresh)
    delete_button.grid(row=0, column=3)
    
    #search form
    
    search_frame = Frame(product_frame, width=350, bd=2, relief=RIDGE)
    search_frame.place(x=400, y=70)
    
    s_title = Label(product_frame, text='Search Products', font=('times new roman', 12, 'bold'))
    s_title.place(x=405, y=57)
    
    search_txt_var = StringVar()
    search_by_var = StringVar(value='selected')
    
    search_by = ttk.Combobox(
        search_frame, values=('Name', 'Category', 'Status'), font=('times new roman', 12, 'bold'), state='readonly',
        textvariable=search_by_var
    )
    search_by.set('Search By')
    search_by.grid(row=0, column=0, padx=5)
    
    search_entry = Entry(search_frame, bg='lightblue', width=30, textvariable=search_txt_var)
    search_entry.grid(row=0, column=1, padx=5)
    
    show_all = Button(
        search_frame, text='Show All', font=('times new roman', 15, 'bold'), bg='navy', fg='white',
        command=lambda: show_all_controller(prod_treeview)
    )
    show_all.grid(row=0, column=2, pady=5, padx=20)
    
    #Treeview
    table_frame = Frame(product_frame)
    table_frame.place(x=350, y=150, height=400, width=600)
    
    horizontal_scroll = Scrollbar(table_frame, orient=HORIZONTAL)
    vertical_scroll = Scrollbar(table_frame, orient=VERTICAL)
    
    prod_treeview = ttk.Treeview(
        table_frame, show='headings', columns=('Ids','Name', 'Price', 'Details', 'Category', 'Supplier', 'Quantity', 'Status'),
        xscrollcommand=horizontal_scroll.set,
        yscrollcommand=vertical_scroll.set
    )
    horizontal_scroll.config(command=prod_treeview.xview)
    vertical_scroll.config(command=prod_treeview.yview)
    horizontal_scroll.pack(fill=X, side=BOTTOM)
    vertical_scroll.pack(fill=Y, side=RIGHT)
    prod_treeview.pack(fill=BOTH, expand=True)
    
    prod_treeview.heading('Ids', text='Ids')
    prod_treeview.heading('Name', text='Name')
    prod_treeview.heading('Price', text='Price')
    prod_treeview.heading('Details', text='Details')
    prod_treeview.heading('Category', text='Category')
    prod_treeview.heading('Supplier', text="Supplier")
    prod_treeview.heading('Quantity', text='Quantity')
    prod_treeview.heading('Status', text='Status')
    
    prod_treeview.column('Ids', width=25)
    prod_treeview.column('Price', width=120)
    treeview_data(prod_treeview)
    
    get_category_and_supplier(prod_cat_entry, prod_sup_entry)
    
    prod_treeview.bind(
        '<ButtonRelease-1>', lambda event: select_data(
            event,
            prod_id,
            prod_name_entry,
            prod_price_entry,
            prod_detail_entry,
            prod_cat_entry,
            prod_sup_entry,
            prod_quantity_entry,
            prod_status
        )
    )
    
    search_entry.bind(
        '<KeyRelease>',
        lambda event:live_search(
            search_by_var.get(),
            search_txt_var.get(),
            prod_treeview
        )
    )
    return product_frame
