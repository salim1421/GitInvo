from tkinter import Frame, ttk, Label, Button, Scrollbar, Entry, messagebox
from database import connect_database
from decimal import Decimal


def treeview_data(treeview):
    conn, cursor = connect_database()
    if not conn or not cursor:
        return
    try:
        cursor.execute(
            'SELECT id, product_name, unit_cost, status, details, quantity, supplier, category, delivered_at FROM purchase_orders ORDER BY id'
        )
        results = cursor.fetchall()
        
        treeview.delete(*treeview.get_children())
        for result in results:
            treeview.insert('', 'end', values=result)
    except Exception as e:
        print(f'Cannot Fetch Purchase Order Due to {e}')
    finally:
        cursor.close()
        conn.close()


def get_category_and_supplier(category_combo, supplier_combo):
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
        category_combo.set('Select')
        for name in names:
            category_option.append(name[0])
        category_combo.config(values=category_option)
        
    cursor.execute(
        'SELECT name FROM supplier_data'
    )
    names = cursor.fetchall()
    if len(names) > 0:
        supplier_combo.set('Select')
        for name in names:
            supplier_option.append(name[0])
        supplier_combo.config(values=supplier_option)


def order_form(window):

    def delete_order(order_id):
        conn, cursor = connect_database()
        if not conn:
            return False
        
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this order?"
        )
        if not confirm:
            return

        try:
            cursor.execute("""
                DELETE FROM purchase_orders
                WHERE id=? AND status != 'Delivered'
            """, (order_id,))

            if cursor.rowcount == 0:
                return False

            conn.commit()
            treeview_data(treeview)
            return True

        except Exception as e:
            conn.rollback()
            print("Delete Error:", e)
            return False

        finally:
            cursor.close()
            conn.close()

    
    def on_delete_button_click():
        selected = treeview.focus()

        if not selected:
            messagebox.showwarning("No Selection", "Please select an order first.")
            return

        order_id = int(treeview.item(selected, "values")[0])

        if delete_order(order_id):
                messagebox.showinfo("Success", "Order deleted.")
        else:
            messagebox.showerror("Error", "Cannot delete delivered or missing order.")


    def clear_fields(
    name_entry,
    price_entry,
    status_combo,
    supplier_combo,
    category_combo,
    stock_entry,
    detail_entry,
    check
    ):
        name_entry.delete(0, 'end')
        price_entry.delete(0, 'end')
        status_combo.set('Select')
        supplier_combo.set('Select')
        category_combo.set('Select')
        stock_entry.delete(0, 'end')
        detail_entry.delete(0, 'end')
        if check:
            treeview.delete(*treeview.get_children())


    def handle_add_order():
        name = name_entry.get()
        cost = price_entry.get()
        qty = stock_entry.get()
        detail = detail_entry.get()
        category_val = category_combo.get() if category_combo.get() != 'Empty' else None
        supplier_val = supplier_combo.get() if supplier_combo.get() != 'Empty' else None

        if not name or not cost or not qty:
            messagebox.showerror("Error", "Name, Price, and Quantity are required.")
            return

        success = create_purchase_order(name, cost, qty, detail, category_val, supplier_val)
        if success:
            messagebox.showinfo("Success", "Purchase order created.")
            # Optionally refresh treeview here
        else:
            messagebox.showerror("Error", "Failed to create order.")


    def create_purchase_order(product_name, unit_cost, quantity, details="", category="", supplier=""):
        conn, cursor = connect_database()
        if not conn or not cursor:
            return False

        try:
            cursor.execute("""
                INSERT INTO purchase_orders
                (product_name, unit_cost, quantity, details, category, supplier, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Pending')
            """, (
                product_name.strip(),
                int(float(unit_cost)),
                int(quantity),
                details.strip(),
                category.strip(),
                supplier.strip()
            ))
            conn.commit()
            treeview_data(treeview)
            return True

        except Exception as e:
            conn.rollback()
            print("Create Purchase Order Error:", e)
            return False

        finally:
            cursor.close()
            conn.close()


    def on_deliver_button_click():
        nonlocal selected_order_id

        if selected_order_id is None:
            messagebox.showwarning("No Order Selected", "Please select a purchase order first.")
            return

        success = mark_purchase_delivered(selected_order_id)

        if success:
            messagebox.showinfo("Success", "Purchase order delivered and stock updated.")
            # Disable the status dropdown in the UI
            status_combo.config(state="disabled")
            # Optionally clear selection
            # selected_order_id = None
        else:
            messagebox.showerror("Error", "Failed to deliver the purchase order.")


    def mark_purchase_delivered(order_id):
        conn, cursor = connect_database()
        if not conn or not cursor:
            return False

        try:
            cursor.execute('BEGIN')

            # Lock purchase order
            cursor.execute("""
                SELECT product_name, unit_cost, quantity, details, category, supplier, status
                FROM purchase_orders
                WHERE id = ?
            """, (order_id,))
            order = cursor.fetchone()
            if not order:
                print("Order not found")
                return False

            product_name, unit_cost, quantity, detail, category, supplier, status = order

            if status == "Delivered":
                print("Order already delivered")
                return False

            # UPSERT into product_data
            cursor.execute("""
                INSERT INTO product_data
                (name, unit_cost, quantity, detail, category, supplier, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Active')
                ON CONFLICT (name)
                DO UPDATE SET
                    quantity = product_data.quantity + EXCLUDED.quantity,
                    unit_cost = EXCLUDED.unit_cost,
                    detail = COALESCE(EXCLUDED.detail, product_data.detail),
                    category = COALESCE(EXCLUDED.category, product_data.category),
                    supplier = COALESCE(EXCLUDED.supplier, product_data.supplier),
                    updated_at = CURRENT_TIMESTAMP
            """, (
                product_name,
                unit_cost,
                quantity,
                detail,
                category,
                supplier
            ))

            # Update purchase order status
            cursor.execute("""
                UPDATE purchase_orders
                SET status = 'Delivered',
                    delivered_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (order_id,))

            conn.commit()

            # Refresh Treeviews
            treeview_data(treeview)       # Purchase Orders
            return True

        except Exception as e:
            conn.rollback()
            print("Delivery Error:", e)
            return False

        finally:
            cursor.close()
            conn.close()


    def load_purchase_order(order_id):
        conn, cursor = connect_database()
        if not conn or not cursor:
            return

        try:
            cursor.execute("""
                SELECT product_name, unit_cost, quantity, details, category, supplier, status
                FROM purchase_orders
                WHERE id = ?
            """, (order_id,))
            order = cursor.fetchone()
            if not order:
                return

            product_name, unit_cost, quantity, detail, category, supplier, status = order

            # Populate UI fields
            name_entry.delete(0, 'end')
            name_entry.insert(0, product_name)

            price_entry.delete(0, 'end')
            price_entry.insert(0, unit_cost)

            stock_entry.delete(0, 'end')
            stock_entry.insert(0, quantity)

            detail_entry.delete(0, 'end')
            detail_entry.insert(0, detail)

            category_combo.set(str(category or ""))
            supplier_combo.set(str(supplier or ""))

            status_combo.set(status)
            status_combo.config(state="disabled" if status == "Delivered" else "readonly")

        finally:
            cursor.close()
            conn.close()


    selected_order_id = None
    def on_order_select(event):
        nonlocal selected_order_id

        selected = treeview.focus()
        if not selected:
            return

        values = treeview.item(selected, "values")

        # assuming first column is id
        selected_order_id = int(values[0])

        load_purchase_order(selected_order_id)


    main_frame = Frame(window, height=587, width=987)
    main_frame.place(x=283, y=100)

    top_label = Label(main_frame, text='Manage Purchase Order', font=('times new roman', 13, 'bold'), fg='white', bg='navy')
    top_label.place(x=0, y=0, relwidth=1)

    back = Button(main_frame, text='Home', font=('times new roman', 9, 'bold'), bg='navy', fg='white', command=lambda:main_frame.place_forget())
    back.place(x=0, y=0)
    
    #filter and search Area
    button_frame = Frame(main_frame)
    button_frame.place(x=150, y=50)

    search_label = Label(button_frame, text='Search Name:', font=('times new roman', 12, 'bold'))
    search_label.grid(column=0, row=0)

    search_entry = Entry(button_frame, bg='lightblue', width=25)
    search_entry.grid(column=1, row=0, padx=10)

    s_delivered = Button(button_frame, text='Show Delivered', font=('times new roman', 12, 'bold'), fg='white', bg='navy')
    s_delivered.grid(column=2, row=0, padx=10)

    s_pending = Button(button_frame, text='Show Pending', font=('times new roman', 12, 'bold'), fg='white', bg='navy')
    s_pending.grid(column=3, row=0)

    #Treeview Area
    table_frame = Frame(main_frame)
    table_frame.place(x=40, y=100, height=300, width=900)

    horizontal_scroll = Scrollbar(table_frame, orient='horizontal')
    vertical_scroll = Scrollbar(table_frame, orient='vertical')

    treeview = ttk.Treeview(
        table_frame, show='headings', columns=('id', 'name', 'unit_cost', 'status', 'detail', 'stock', 'supplier', 'category', 'Date'),
        yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set
    )
    horizontal_scroll.config(command=treeview.xview)
    vertical_scroll.config(command=treeview.yview)
    horizontal_scroll.pack(fill='x', side='bottom')
    vertical_scroll.pack(fill='y', side='right')

    treeview.pack(fill='both', expand=True)
    treeview_data(treeview)

    treeview.heading('id', text='Id')
    treeview.heading('name', text='Name')
    treeview.heading('unit_cost', text='Price')
    treeview.heading('status', text='Status')
    treeview.heading('detail', text='Details')
    treeview.heading('stock', text='Stock')
    treeview.heading('supplier', text='Supplier')
    treeview.heading('category', text='Category')
    treeview.heading('Date', text='Delivered On')

    treeview.column('id', width=30)

    #order input fields
    crud_frame = Frame(main_frame)
    crud_frame.place(x=100, y=420)

    name_label = Label(crud_frame, text='Name', font=('times new roman', 12, 'bold'))
    name_label.grid(row=0, column=0)

    name_entry = Entry(crud_frame, bg='lightblue', width=25)
    name_entry.grid(row=0, column=1, padx=5)

    price_label = Label(crud_frame, text='Price', font=('times new roman', 12, 'bold'))
    price_label.grid(row=0, column=2)

    price_entry = Entry(crud_frame, bg='lightblue', width=25)
    price_entry.grid(row=0, column=3, padx=5)

    status_label = Label(crud_frame, text='Status', font=('times new roman', 12, 'bold'))
    status_label.grid(row=0, column=4)

    status_combo = ttk.Combobox(crud_frame, values=('Pending', 'Delivered'), font=('times new roman', 12, 'bold'), state='readonly')
    status_combo.set('Select')
    status_combo.grid(row=0, column=5, padx=5)

    category_label = Label(crud_frame, text='Category', font=('times new roman', 12, 'bold'))
    category_label.grid(row=1, column=0)

    category_combo = ttk.Combobox(crud_frame, font=('times new roman', 12, 'bold'), state='readonly')
    category_combo.set('Empty')
    category_combo.grid(row=1, column=1, padx=5)

    sup_label = Label(crud_frame, text='Supplier', font=('times new roman', 12, 'bold'))
    sup_label.grid(row=1, column=2)

    supplier_combo = ttk.Combobox(crud_frame, font=('times new roman', 12, 'bold'), state='readonly')
    supplier_combo.set('Empty')
    supplier_combo.grid(row=1, column=3, padx=5)
    get_category_and_supplier(category_combo, supplier_combo)

    stock_label = Label(crud_frame, text='Quantity', font=('times new roman', 12, 'bold'))
    stock_label.grid(row=1, column=4)

    stock_entry = Entry(crud_frame, bg='lightblue', width=25)
    stock_entry.grid(row=1, column=5, padx=5)

    detail_label = Label(crud_frame, text='Detail', font=('times new roman', 12, 'bold'))
    detail_label.grid(row=2, column=0)

    detail_entry = Entry(crud_frame, bg='lightblue', width=25)
    detail_entry.grid(row=2, column=1, padx=5)

    #CRUD Buttons
    c_button_frame = Frame(main_frame, pady=10)
    c_button_frame.place(x=100, y=500)

    add_button = Button(
        c_button_frame, text='Add', font=('times new roman', 12, 'bold'), width=15, fg='white', bg="#0A4F0F",
        command=handle_add_order
    )
    add_button.grid(row=0, column=0, padx=10)

    delivered_btn = Button(
        c_button_frame, text='Update', font=('times new roman', 12, 'bold'), width=15, fg='white', bg="navy",
        command=on_deliver_button_click
        )
    delivered_btn.grid(row=0, column=1, padx=10)

    clear_button = Button(
        c_button_frame, text='Clear', font=('times new roman', 12, 'bold'), fg='white', width=15, bg="#797F7A",
        command=lambda:clear_fields(
            name_entry, price_entry, status_combo, supplier_combo, category_combo, stock_entry, detail_entry, False
        )
    )
    clear_button.grid(row=0, column=2, padx=10)
            

    delete_button = Button(
        c_button_frame, text='Delete', font=('times new roman', 12, 'bold'), fg='white', bg="#370404",
        command=on_delete_button_click, width=15
    )
    delete_button.grid(row=0, column=3)

    treeview.bind('<<TreeviewSelect>>', on_order_select)


    return main_frame
