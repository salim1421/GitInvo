from tkinter import *
from tkinter import messagebox, ttk
from tkinter import simpledialog
from employee import connect_database
from decimal import Decimal


def setup_database():
    conn, cursor = connect_database()
    if not conn or not cursor:
        return
    try:
        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS refunds (
        id SERIAL PRIMARY KEY,
        sale_id INTEGER REFERENCES sales(id),
        customer_name VARCHAR(100),
        refund_total NUMERIC(12,2),
        refund_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS refund_items(
            id SERIAL PRIMARY KEY,
            refund_id INTEGER REFERENCES refunds(id),
            product_id INTEGER,
            product_name VARCHAR(150),
            quantity INTEGER,
            unit_cost NUMERIC(12,2),
            unit_price NUMERIC(12,2),
            total NUMERIC(12,2),
            profit NUMERIC(12,2)
            )
        """
        )

        conn.commit()
        return True
    
    finally:
        conn.close()
        cursor.close()

setup_database()


def process_refund(sale_id, refund_cart):
    conn, cursor = connect_database()
    if not conn:
        return

    try:
        # Check if sale exists
        cursor.execute("SELECT id FROM sales WHERE id = %s", (sale_id,))
        if cursor.fetchone() is None:
            raise Exception("Sale ID not found.")

        refund_total = Decimal("0.00")

        # Insert refund header
        cursor.execute("""
            INSERT INTO refunds (sale_id, customer_name, refund_total)
            SELECT id, customer_name, 0
            FROM sales
            WHERE id = %s
            RETURNING id
        """, (sale_id,))

        refund_id = cursor.fetchone()[0]

        # Process each refunded item
        for pid, item in refund_cart.items():

            # Check sold quantity
           # Get sold quantity
            cursor.execute("""
                SELECT quantity, selling_price, unit_cost
                FROM sales_items
                WHERE sale_id = %s AND product_id = %s
            """, (sale_id, pid))

            sale_result = cursor.fetchone()

            if sale_result is None:
                raise Exception("Product not found in sale.")

            sold_qty, selling_price, unit_cost = sale_result

            # Get already refunded quantity
            cursor.execute("""
                SELECT COALESCE(SUM(quantity), 0)
                FROM refund_items ri
                JOIN refunds r ON ri.refund_id = r.id
                WHERE r.sale_id = %s AND ri.product_id = %s
            """, (sale_id, pid))

            refunded_qty = cursor.fetchone()[0]

            available_to_refund = sold_qty - refunded_qty

            if item["qty"] > available_to_refund:
                raise Exception(
                    f"Only {available_to_refund} item(s) available for refund."
                )
            line_total = selling_price * item["qty"]
            line_profit = (selling_price - unit_cost) * item["qty"]

            # Insert refund item
            cursor.execute("""
                    INSERT INTO refund_items
                    (refund_id, product_id, product_name, quantity,
                    unit_cost, unit_price, total, profit)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    refund_id,
                    pid,
                    item["name"],
                    item["qty"],
                    unit_cost,
                    selling_price,
                    line_total,
                    line_profit
                ))

            # Restore stock
            cursor.execute("""
                UPDATE product_data
                SET quantity = quantity + %s
                WHERE id = %s
            """, (item["qty"], pid))

        # Update refund total
        cursor.execute("""
            UPDATE refunds
            SET refund_total = %s
            WHERE id = %s
        """, (refund_total, refund_id))

        conn.commit()
        cursor.close()
        conn.close()

        return refund_id, refund_total

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e


def load_sales_history(period):
    conn, cursor = connect_database()

    try:
        if period == "daily":
            condition = "DATE(s.created_at) = CURRENT_DATE"
        elif period == "monthly":
            condition = "DATE_TRUNC('month', s.created_at) = DATE_TRUNC('month', CURRENT_DATE)"
        elif period == "annual":
            condition = "DATE_TRUNC('year', s.created_at) = DATE_TRUNC('year', CURRENT_DATE)"
        else:
            condition = "1=1"

        query = f"""
            SELECT 
                s.id,
                s.customer_name,
                s.phone,

                s.subtotal,
                s.tax,

                -- Adjusted Total (sale - refund)
                s.total - COALESCE(SUM(ri.total),0) AS adjusted_total,

                -- Adjusted Profit (sale profit - refund profit)
                COALESCE(SUM(si.profit),0)
                -
                COALESCE(SUM(ri.profit),0) AS adjusted_profit,

                s.created_at,

                CASE
                    WHEN COALESCE(SUM(si.quantity),0) =
                        COALESCE(SUM(ri.quantity),0)
                        AND COALESCE(SUM(si.quantity),0) > 0
                    THEN 'FULL'
                    WHEN COALESCE(SUM(ri.quantity),0) > 0
                    THEN 'PARTIAL'
                    ELSE 'NONE'
                END AS refund_status

            FROM sales s
            LEFT JOIN sales_items si ON s.id = si.sale_id
            LEFT JOIN refunds r ON s.id = r.sale_id
            LEFT JOIN refund_items ri 
                ON r.id = ri.refund_id 
                AND ri.product_id = si.product_id

            WHERE {condition}

            GROUP BY s.id
            ORDER BY s.created_at DESC
            """

        cursor.execute(query)
        rows = cursor.fetchall()

        total_revenue = sum(Decimal(row[5]) for row in rows)
        total_profit = sum(Decimal(row[6]) for row in rows)
        total_cost = total_revenue - total_profit

        profit_margin = 0
        if total_revenue > 0:
            profit_margin = (total_profit / total_revenue) * 100

        return rows, total_revenue, total_profit, total_cost, profit_margin

    finally:
        cursor.close()
        conn.close()


def fetch_profit_by_period(period):
    conn, cursor = connect_database()

    try:
        if period == "daily":
            condition = "DATE(s.created_at) = CURRENT_DATE"
        elif period == "monthly":
            condition = "DATE_TRUNC('month', s.created_at) = DATE_TRUNC('month', CURRENT_DATE)"
        elif period == "annual":
            condition = "DATE_TRUNC('year', s.created_at) = DATE_TRUNC('year', CURRENT_DATE)"
        else:
            condition = "1=1"

        query = f"""
            SELECT
                COALESCE(SUM(si.profit), 0)
                -
                COALESCE(SUM(ri.profit), 0)
            FROM sales s
            LEFT JOIN sales_items si ON s.id = si.sale_id
            LEFT JOIN refunds r ON s.id = r.sale_id
            LEFT JOIN refund_items ri ON r.id = ri.refund_id
            WHERE {condition}
        """

        cursor.execute(query)
        result = cursor.fetchone()[0]

        return result or Decimal("0.00")

    finally:
        cursor.close()
        conn.close()


        

def sales_history_form(window):


    def load_sale_items(event):
        selected = history_treeview.focus()
        if not selected:
            return

        values = history_treeview.item(selected, "values")
        sale_id = values[0]

        conn, cursor = connect_database()

        cursor.execute("""
            SELECT product_id, product_name, quantity, selling_price, total
            FROM sales_items
            WHERE sale_id = %s
        """, (sale_id,))

        rows = cursor.fetchall()

        treeview.delete(*treeview.get_children())

        for row in rows:
            treeview.insert("", "end", values=row)

        cursor.close()
        conn.close()


    def refund_selected():
        selected_sale = history_treeview.focus()
        selected_item = treeview.focus()

        if not selected_sale or not selected_item:
            messagebox.showerror("Error", "Select sale and item first.")
            return

        sale_id = history_treeview.item(selected_sale, "values")[0]
        item_values = treeview.item(selected_item, "values")

        product_id = item_values[0]
        product_name = item_values[1]
        sold_qty = int(item_values[2])
        selling_price = Decimal(item_values[3])

        # Ask how many to refund
        refund_qty = simpledialog.askinteger(
            "Refund Quantity",
            f"Enter quantity to refund (Max {sold_qty}):",
            minvalue=1,
            maxvalue=sold_qty
        )

        if not refund_qty:
            return

        refund_cart = {
            product_id: {
                "name": product_name,
                "qty": refund_qty
            }
        }

        try:
            refund_id, refund_total = process_refund(sale_id, refund_cart)

            messagebox.showinfo(
                "Refund Success",
                f"Refund ID: {refund_id}\nAmount: {refund_total:.2f}"
            )

        except Exception as e:
            messagebox.showerror("Refund Error", str(e))

    
    history_frame = Frame(window)
    history_frame.place(x=283, y=0, height=890, width=987)

    title = Label(
        history_frame,
        text="Sales History",
        font=("times new roman", 15, "bold"),
        bg="navy",
        fg="white"
    )
    title.pack(fill=X)

    back = Button(
        history_frame, text='Back', font=('times new roman', 10, 'bold'), fg='white', bg='navy',
        command=lambda:history_frame.place_forget()
    )
    back.place(x=0, y=0)


    filter_frame = Frame(history_frame)
    filter_frame.place(x=350, y=100)

    period_var = StringVar(value="all")

    Radiobutton(filter_frame, text="Daily", variable=period_var, value="daily").grid(row=0, column=0, padx=10)
    Radiobutton(filter_frame, text="Monthly", variable=period_var, value="monthly").grid(row=0, column=1, padx=10)
    Radiobutton(filter_frame, text="Annual", variable=period_var, value="annual").grid(row=0, column=2, padx=10)
    Radiobutton(filter_frame, text="All", variable=period_var, value="all").grid(row=0, column=3, padx=10)

    summary_frame = Frame(history_frame)
    summary_frame.pack(fill="x", pady=5)

    revenue_label = Label(summary_frame, text="Revenue: 0")
    revenue_label.pack(side="left", padx=20)

    profit_label = Label(summary_frame, text="Profit: 0")
    profit_label.pack(side="left", padx=20)

    cost_label = Label(summary_frame, text="Cost: 0")
    cost_label.pack(side="left", padx=20)

    margin_label = Label(summary_frame, text="Margin: 0%")
    margin_label.pack(side="left", padx=20)


    table_frame = Frame(history_frame)
    table_frame.place(x=50, y=145, height=250, width=900)

    horizontal_scroll = Scrollbar(table_frame, orient=HORIZONTAL)
    vertical_scroll = Scrollbar(table_frame, orient=VERTICAL)
    history_treeview = ttk.Treeview(
        table_frame,
        columns=("ID", "Customer", "Phone", "Subtotal", "Tax", "Total", 'Profit', "Date", 'refund_status'),
        show="headings", xscrollcommand=horizontal_scroll.set, yscrollcommand=vertical_scroll.set
    )

    horizontal_scroll.config(command=history_treeview.xview)
    vertical_scroll.config(command=history_treeview.yview)

    horizontal_scroll.pack(fill=X, side=BOTTOM)
    vertical_scroll.pack(fill=Y, side=RIGHT)
    history_treeview.pack(fill=BOTH, expand=True)


    history_treeview.heading('ID', text='Ids')
    history_treeview.heading('Customer', text='Customer')
    history_treeview.heading('Phone', text='Phone')
    history_treeview.heading('Subtotal', text='Subtotal')
    history_treeview.heading('Tax', text='Tax')
    history_treeview.heading('Total', text='Total')
    history_treeview.heading('Profit', text='Profit')
    history_treeview.heading('Date', text='Date')
    history_treeview.heading('refund_status', text='Refund Status')
    
    total_label = Label(history_frame, text="Total Revenue: 0.00", font=("times new roman", 12, "bold"))
    total_label.pack(pady=5)

    def load_data():
        period = period_var.get()

        rows, total_revenue, total_profit, total_cost, profit_margin = load_sales_history(period)

        history_treeview.delete(*history_treeview.get_children())

        for row in rows:
            item_id = history_treeview.insert("", "end", values=row)

            status = row[8]

            if status == "FULL":
                history_treeview.item(item_id, tags=("full",))
            elif status == "PARTIAL":
                history_treeview.item(item_id, tags=("partial",))

        history_treeview.tag_configure("full", background="#ffd6d6")
        history_treeview.tag_configure("partial", background="#fff3cd")

        revenue_label.config(text=f"Revenue: {total_revenue:.2f}")
        profit_label.config(text=f"Profit: {total_profit:.2f}")
        cost_label.config(text=f"Cost: {total_cost:.2f}")
        margin_label.config(text=f"Margin: {profit_margin:.2f}%")

        total_label.config(text=f"Total Revenue: {total_revenue:.2f}")

    Button(filter_frame, text="Load", command=load_data).grid(row=0, column=4, padx=20)

    history_treeview.bind("<<TreeviewSelect>>", load_sale_items)

    #Refund treeview
    refund_title = Label(history_frame, text='Refund Section', font=('times new roman',  14, 'bold'))
    refund_title.place(x=400, y=399)

    t_frame = Frame(history_frame)
    t_frame.place(x=50, y=430, height=250, width=900)

    horizontal_scroll = Scrollbar(t_frame, orient=HORIZONTAL)
    vertical_scroll = Scrollbar(t_frame, orient=VERTICAL)
    treeview = ttk.Treeview(
        t_frame,
        columns=("ID", "product id", "name", "quantity", "price", "total"),
        show="headings", xscrollcommand=horizontal_scroll.set, yscrollcommand=vertical_scroll.set
    )

    horizontal_scroll.config(command=treeview.xview)
    vertical_scroll.config(command=treeview.yview)

    horizontal_scroll.pack(fill=X, side=BOTTOM)
    vertical_scroll.pack(fill=Y, side=RIGHT)
    treeview.pack(fill=BOTH, expand=True)


    treeview.heading('ID', text='Ids')
    treeview.heading('product id', text='Product id')
    treeview.heading('name', text='Name')
    treeview.heading('quantity', text='Quantity')
    treeview.heading('price', text='Price')
    treeview.heading('total', text='Total')

    refund_button = Button(
        history_frame, text="Refund Selected", font=('times new roman', 12, 'bold'), fg='white', bg='navy', command=refund_selected
    )
    refund_button.place(x=800, y=395)

    return history_frame