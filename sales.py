from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from fpdf import FPDF # type: ignore
from database import connect_database
from datetime import datetime
import tempfile
import os


font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")

def logout(window):
    confirm = messagebox.askyesno(
        'Confirm Log Out',
        'Are you sure you want to logout?'
    )
    if not confirm:
        return

    for widget in window.winfo_children():
        widget.destroy()

# Import login UI builder function
    from login import login_ui
    login_ui(window)
    

def product_treeview(prod_treeview):
    conn, cursor = connect_database()
    if not conn or not cursor:
        return
    
    try:
        cursor.execute(
            '''
            SELECT id, name, unit_cost, detail, category, supplier, quantity, status FROM product_data
            ORDER BY id
            '''
        )
        products = cursor.fetchall()
        for product in products:
            prod_treeview.insert('', END, values=product)
    except Exception as e:
        print(f'Cannot Fetch Products, Due to {e}')



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



def live_search_products(name):
    conn, cursor = connect_database()
    if not conn:
        return []

    try:
        cursor.execute("""
            SELECT id, name, unit_cost, detail, category, supplier, quantity, status
            FROM product_data
            WHERE CAST(name AS TEXT) LIKE ?
            ORDER BY id
        """, (f"%{name}%",))
        
        return cursor.fetchall()

    except Exception as e:
        print("Live Search Error:", e)
        return []

    finally:
        cursor.close()
        conn.close()


def live_search_controller(keyword, product_treeview):
    # If no search type selected → show all
    if keyword.strip() == "":
        product_treeview.delete(*product_treeview.get_children())
        for row in get_all_products():
            product_treeview.insert("", "end", values=row)
        return

    results = live_search_products(keyword)

    product_treeview.delete(*product_treeview.get_children())

    for row in results:
        product_treeview.insert("", "end", values=row)


def show_all_controller(cat_treeview):
    cat_treeview.delete(*cat_treeview.get_children())

    for row in get_all_products():
        cat_treeview.insert("", "end", values=row)




def sales_form(window, cashier_name):

    def to_kobo(value):
            value = value.strip()
            if not value:
                return 0
            return int(float(value) * 100)
    
    selected_product = {"id": None, "name": None, "unit_cost": None, 'selling_price': None}
    def select_product(event):
        selected = prod_treeview.focus()
        if not selected:
            return

        row = prod_treeview.item(selected, "values")
        if not row:
            return

        product_id = row[0]

        # Fill UI
        p_name_entry.delete(0, END)

        p_name_entry.insert(0, row[1])

        # Fetch unit_cost from DB
        product_id = int(row[0])

        conn, cursor = connect_database()
        cursor.execute(
            "SELECT unit_cost, selling_price FROM product_data WHERE id = ?",
            (product_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result is None:
            unit_cost = 0
            selling_price = 0
        else:
            unit_cost = int(result[0])
            selling_price = int(result[1])

        selected_product["id"] = product_id
        selected_product["name"] = row[1]
        selected_product["unit_cost"] = unit_cost
        selected_product["selling_price"] = selling_price

        # show in UI (naira)
        cost_price_entry.delete(0, END)
        cost_price_entry.insert(0, selling_price * 100)


    cart = {}
    def add_to_cart():
        try:
            prod_id = selected_product["id"]
            name = p_name_entry.get()
            unit_cost = selected_product["unit_cost"]
            selling_price = int(cost_price_entry.get())
            qty = int(p_quantity_entry.get())
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Invalid price or quantity")
            return

        if not prod_id:
            messagebox.showerror("Error", "Select a product first")
            return

        if qty <= 0:
            messagebox.showerror("Error", "Quantity must be greater than zero")
            return

        if prod_id in cart:
            cart[prod_id]["qty"] += qty
        else:
            cart[prod_id] = {
                "name": name,
                "unit_cost": unit_cost,
                "selling_price": selling_price,
                "qty": qty,
                "total": selling_price * qty
            }

        cart[prod_id]["total"] = cart[prod_id]["selling_price"] * cart[prod_id]["qty"]
        refresh_cart_treeview()
        clear_cart_inputs()
    
    
    def refresh_cart_treeview():
        treeview.delete(*treeview.get_children())

        for pid, item in cart.items():
            treeview.insert(
                "",
                END,
                values=(
                    pid,
                    item["name"],
                    item["selling_price"],
                    item["qty"],
                    item["total"]
                )
            )

    def clear_cart_inputs():
        p_name_entry.delete(0, END)
        cost_price_entry.delete(0, END)
        p_quantity_entry.delete(0, END)
 
        
    selected_cart_id = None
    
    def select_cart_item(event):
        nonlocal selected_cart_id

        selected = treeview.focus()
        if not selected:
            return

        row = treeview.item(selected, "values")
        selected_cart_id = row[0]   # product id
        
    
    def remove_from_cart():
        if not selected_cart_id:
            messagebox.showerror("Error", "Select an item from cart to remove")
            return

        del cart[selected_cart_id]
        refresh_cart_treeview()

    
    def generate_bill(customer_name, contact, cashier_name, cart, bill):

        def format_currency(kobo):
            return f"NGN{kobo:,.2f}"

        if customer_name == "" or contact == "":
            messagebox.showerror("Error", "Customer details are required")
            return

        if not cart:
            messagebox.showerror("Error", "Cart is empty")
            return

        try:
            sale_id, subtotal, tax, grand_total = complete_sale(
                customer_name,
                contact,
                cart
            )
        except Exception as e:
            messagebox.showerror("Stock Error", str(e))
            return



        # 🔹 Generate receipt
        bill.config(state='normal')
        bill.delete(1.0, 'end')

        bill.insert('end', "\t  TkComms \n")
        bill.insert('end', "\t Sales Receipt\n")
        bill.insert('end', "="*42 + "\n")
        bill.insert('end', f"Bill No : {sale_id}\n")
        bill.insert('end', f"Date    : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        bill.insert('end', f'Cashier : {cashier_name}\n')
        bill.insert('end', f"Customer: {customer_name}\n")
        bill.insert('end', f"Contact : {contact}\n")
        bill.insert('end', "="*42 + "\n")

        bill.insert('end', f"{'Product':<12}{'Qty':<6}{'Price':<8}{'Total':<8}\n")
        bill.insert('end', "="*42 + "\n")

        for item in cart.values():
            bill.insert(
                'end',
                f"{item['name']:<12}{item['qty']:<6}{item['selling_price']:<8}{item['total']:<8}\n"
            )

        bill.insert('end', "="*42 + "\n")
        bill.insert('end', f"{'Subtotal:':<26}{format_currency(subtotal)}\n")
        bill.insert('end', f"{'Tax:':<26}{format_currency(tax)}\n")
        bill.insert('end', f"{'Grand Total:':<26}{format_currency(grand_total)}\n")
        bill.insert('end', "="*42 + "\n")
        bill.insert('end', "\t Thank You! Visit Again\n")

        bill.config(state='disabled')

        # 🔹 Generate PDF
        pdf = FPDF()
        pdf.add_page()

        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.set_font("Courier", size=12)

        for line in bill.get(1.0, 'end').splitlines():
            pdf.cell(0, 6, txt=line, ln=1)

        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_file_path = temp_pdf.name
        temp_pdf.close()
        pdf.output(pdf_file_path)

        # 🔹 Auto-open PDF
        os.startfile(pdf_file_path)

        # 🔹 Clear cart after printing
        cart.clear()
        treeview.delete(*treeview.get_children())


    def clear_all():
        bill.config(state='normal')
        bill.delete(1.0, 'end')
        bill.config(state='disabled')

        cart.clear()
        refresh_cart_treeview()


    def print_bill():
        if bill.get(1.0, 'end').strip() == "":
            messagebox.showerror("Error", "Bill is empty")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(bill.get(1.0, 'end').encode())
            temp_file = f.name

        with open(temp_file, 'w') as f:
            f.write(bill.get(1.0, 'end'))

        os.startfile(temp_file, 'print')


    def deduct_stock(cart, cursor):
        for pid, item in cart.items():
            cursor.execute("""
                UPDATE product_data
                SET quantity = quantity - ?
                WHERE id = ?
            """, (item["qty"], pid))


    def complete_sale(customer_name, phone, cart):
        conn, cursor = connect_database()
        if not conn or not cursor:
            return

        if not cart:
            messagebox.showerror("Error", "Cart is empty")
            return

        subtotal = 0
        total_profit = 0
        
        
        # Calculate subtotal and profit
        for item in cart.values():
            subtotal += item["total"]
            item_profit = (item["selling_price"] - item["unit_cost"]) * item["qty"]
            total_profit += item_profit

        #DB tax
        cursor.execute(
                'SELECT tax FROM tax_data WHERE id=1'
            )
        gettax = cursor.fetchone()[0]

        tax = int(subtotal * (gettax/100))
        total = subtotal + tax

        # Insert into sales table (MATCHING YOUR COLUMNS)
        cursor.execute(
            """
            INSERT INTO sales (customer_name, phone, subtotal, tax, total)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id
            """,
            (customer_name, phone, subtotal, tax, total)
        )

        sale_id = cursor.fetchone()[0]

        # Insert items into sales_items
        for prod_id, item in cart.items():
            item_profit = (item["selling_price"] - item["unit_cost"]) * item["qty"]

            cursor.execute(
                """
                INSERT INTO sales_items
                (sale_id, product_id, product_name, unit_cost, selling_price, quantity, total, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sale_id,
                    prod_id,
                    item["name"],
                    item["unit_cost"],
                    item["selling_price"],
                    item["qty"],
                    item["total"],
                    item_profit
                )
            )

        deduct_stock(cart, cursor)
        conn.commit()
        cursor.close()
        conn.close()

        messagebox.showinfo("Success", f"Sale completed!\nProfit: {total_profit:.2f}")

        return sale_id, subtotal, tax, total



    sales_frame = Frame(window, height=1270, width=1270)
    sales_frame.place(x=0, y=0)
    
    title_label = Label(
        sales_frame,
        text="Point Of Sales(POS)",
        font=("times new roman", 15, "bold"),
        bg="#A1A1A1",
    )
    title_label.place(x=0, y=0, relwidth=1)

    back = Button(
        sales_frame,
        text="Home",
        font=("times new roman", 10, "bold"),
        fg="white",
        bg="navy",
        command=sales_frame.place_forget,
    )
    back.place(x=0, y=0)
    
    #search fields
    search_frame = Frame(sales_frame, bd=2, relief=RIDGE)
    search_frame.place(x=10, y=50, width=400)
    
    s_title = Label(sales_frame, text='Products', font=('times new roman', 12, 'bold'), fg='white', bg='navy')
    s_title.place(x=10, y=32, width=400)
    
    search_label = Label(search_frame, text='Product Name', font=('times new roman', 12, 'bold'))
    search_label.grid(row=1, column=0, padx=5, pady=10)
    
    search_txt_var = StringVar()
    search_entry = Entry(search_frame, bg='lightblue', width=25, textvariable=search_txt_var)
    search_entry.grid(row=1, column=1, padx=10)
    
    show_all = Button(search_frame, text='Show All', font=('times new roman', 12, 'bold'), bg='navy', fg='white')
    show_all.grid(row=1, column=2, padx=10)
    
    
    #product treeview
    
    prod_frame = Frame(sales_frame)
    prod_frame.place(x=10, y=100, width=400, height=450)
    
    horizontal_scroll = Scrollbar(prod_frame, orient=HORIZONTAL)
    vertical_scroll = Scrollbar(prod_frame, orient=VERTICAL)
    
    prod_treeview = ttk.Treeview(
        prod_frame, show='headings', columns=('Ids','Name', 'Price', 'Details', 'Category', 'Supplier', 'Quantity', 'Status'),
        xscrollcommand=horizontal_scroll.set, yscrollcommand=vertical_scroll.set
        
    )
    horizontal_scroll.config(command=prod_treeview.xview)
    vertical_scroll.config(command=prod_treeview.yview)
    horizontal_scroll.pack(fill=X, side=BOTTOM)
    vertical_scroll.pack(fill=Y, side=RIGHT)
    prod_treeview.pack(fill=BOTH, expand=True)
    
    product_treeview(prod_treeview)
    prod_treeview.heading('Ids', text='Ids')
    prod_treeview.heading('Name', text='Name')
    prod_treeview.heading('Price', text='Price')
    prod_treeview.heading('Details', text='Details')
    prod_treeview.heading('Category', text='Category')
    prod_treeview.heading('Supplier', text="Supplier")
    prod_treeview.heading('Quantity', text='In Stock')
    prod_treeview.heading('Status', text='Status')
    
    prod_treeview.column('Ids', width=30)
    prod_treeview.column('Price', width=80)
    prod_treeview.column('Category', width=90)
    prod_treeview.column('Quantity', width=90)
    prod_treeview.column('Status', width=70)
    
    #customer details
    
    c_frame = Frame(sales_frame)
    c_frame.place(x=410, y=410, width=400)
    
    p_name = Label(c_frame, text='Product Name', font=('times new roman', 12, 'bold'))
    p_name.grid(row=0, column=0)
    
    p_price = Label(c_frame, text='Price', font=('times new roman', 12, 'bold'))
    p_price.grid(row=0, column=1)
    
    p_quantity = Label(c_frame, text='Quantity', font=('times new roman', 12, 'bold'))
    p_quantity.grid(row=0, column=2)
    
    p_name_entry = Entry(c_frame, bg='lightblue')
    p_name_entry.grid(row=1, column=0, padx=5)
    
    cost_price_entry = Entry(c_frame, bg='lightblue')
    cost_price_entry.grid(row=1, column=1, padx=5)
    
    p_quantity_entry = Entry(c_frame, bg='lightblue')
    p_quantity_entry.grid(row=1, column=2)
    
    add_button = Button(
        c_frame, text='Add/Update Cart', font=('times new roman', 12, 'bold'), fg='white', bg='darkblue',
    )
    add_button.config(command=add_to_cart)
    add_button.grid(row=2, column=0, padx=5, pady=10)
    
    
    clear_button = Button(
        c_frame, text='Clear Cart', font=('times new roman', 12, 'bold'), fg='white', bg='darkblue',
        command=lambda: clear_cart_inputs()
    )
    clear_button.grid(row=2, column=1, padx=5, pady=10)
    
    remove_button = Button(
        c_frame, text='Remove', font=('times new roman', 12, 'bold'), fg='white', bg='darkblue',
        command=lambda: remove_from_cart()
    )
    remove_button.grid(row=2, column=2)
    
    
    #Cart GUI
    title_frame = Frame(sales_frame, bd=2, relief=RIDGE)
    title_frame.place(x=420, y=53, width=400)
    
    title = Label(sales_frame, font=('times new roman', 12, 'bold'), text='Cart Check Out', bg='navy', fg='white')
    title.place(x=420, y=32, width=400)
    
    c_name = Label(title_frame, text='Customer Name', font=('times new roman', 12, 'bold'))
    c_name.grid(row=0, column=0)
    
    c_entry = Entry(title_frame, bg='lightblue')
    c_entry.grid(row=0, column=1, padx=5)
    
    contact = Label(title_frame, text='Phone Number', font=('times new roman', 12, 'bold'))
    contact.grid(row=1, column=0)
    
    contact_entry = Entry(title_frame, bg='lightblue')
    contact_entry.grid(row=1, column=1)
    
    #main cart treeview
    table_frame = Frame(sales_frame)
    table_frame.place(x=420, y=110, width=405, height=300)
    
    horizontal_scroll = Scrollbar(table_frame, orient=HORIZONTAL)
    vertical_scroll = Scrollbar(table_frame, orient=VERTICAL)
    
    treeview = ttk.Treeview(
        table_frame, show='headings', columns=('Ids','Name', 'Price', 'Quantity', 'Total'),
        xscrollcommand=horizontal_scroll.set,
        yscrollcommand=vertical_scroll.set   
    )
    horizontal_scroll.config(command=treeview.xview)
    vertical_scroll.config(command=treeview.yview)
    horizontal_scroll.pack(fill=X, side=BOTTOM)
    vertical_scroll.pack(fill=Y, side=RIGHT)
    treeview.pack(fill=BOTH, expand=True)
    
    treeview.heading('Ids', text='Ids')
    treeview.heading('Name', text='Name')
    treeview.heading('Price', text='Price')
    treeview.heading('Quantity', text='Quantity')
    treeview.heading('Total', text='Total')
    
    treeview.column('Ids', width=30)
    treeview.column('Price', width=70)
    treeview.column('Quantity', width=90)


    #billing frame GUI
    
    b_frame = Frame(
        sales_frame
    )
    b_frame.place(x=840, y=32, width=420, height=400)
    
    b_title = Label(b_frame, text='Bill/Receipt', font=('times new roman', 12, 'bold'), bg='navy', fg='white')
    b_title.pack(fill=X)
    
    bill = Text(
        b_frame, font=('Courier New', 12, 'bold'), state='disabled'
    )
    bill.pack(fill=X, expand=True)
    
    
    #button frame
    
    button_frame = Frame(sales_frame)
    button_frame.place(x=840, y=450)
    
    g_bill = Button(
        button_frame, text='Generate Bill', font=('times new roman', 15, 'bold'), fg='white', bg='blue',
        command=lambda: generate_bill(
            c_entry.get(),
            contact_entry.get(),
            cashier_name,
            cart,
            bill
        )
    )
    g_bill.grid(row=0, column=0, padx=10)
    
    print_button = Button(
        button_frame, text='Print/Save', font=('times new roman', 15, 'bold'), fg='white', bg='blue', width=10,
        command=lambda:print_bill()
    )
    print_button.grid(row=0, column=1, padx=10)
    
    clear_button = Button(
        button_frame, text='Clear All', font=('times new roman', 15, 'bold'), fg='white', bg='blue', width=7,
        command=clear_all
    )
    clear_button.grid(row=0, column=2)

    logout_button = Button(
        sales_frame, text='Log Out', font=('times new roman', 25, 'bold'), fg='white', bg='navy', width=15, height=2,
        command=lambda:logout(window)
        )
    logout_button.place(x=900, y=550)
    
    prod_treeview.bind("<ButtonRelease-1>", select_product)
    treeview.bind("<ButtonRelease-1>", select_cart_item)
    search_entry.bind(
        '<KeyRelease>',
        lambda event:live_search_controller(
            search_txt_var.get(),
            prod_treeview
        )
    )

