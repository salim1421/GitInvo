from tkinter import *
from employee import employee_form
from supplier import supplier_form
from category import category_form
from products import product_form
from employee import connect_database
from tkinter import messagebox
from datetime import datetime
from sales import sales_form
from sales_history import sales_history_form
from purchase_order import order_form



current_frame = None
def show_form(window, form_function, *args):
    global current_frame

    if current_frame and current_frame.winfo_exists():
        current_frame.destroy()

    current_frame = form_function(window, *args)

def exit(window):
    confirm = messagebox.askyesno(
        "Confirm Exit",
        "Are you sure you want to exit?"
    )

    if not confirm:
        return

    window.destroy()


def logout(window):
    global current_frame

    confirm = messagebox.askyesno(
        'Confirm Log Out',
        'Are you sure you want to logout?'
    )
    if not confirm:
        return

    # Destroy everything
    for widget in window.winfo_children():
        widget.destroy()

    # IMPORTANT: reset reference
    current_frame = None

    from login import login_ui
    login_ui(window)


def total_employees():
    conn, cursor = connect_database()
    try:
        cursor.execute(
            'SELECT COUNT(*) FROM employee_data'
        )
        employees = cursor.fetchone()[0]
        return employees
    except Exception as e:
        print(f'cannot fetch total employees, {e}')
        return 0
    

def total_categories():
    conn, cursor = connect_database()
    try:
        cursor.execute(
            'SELECT COUNT(*) FROM category_data'
        )
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        return 0
    

def total_products():
    conn, cursor = connect_database()
    try:
        cursor.execute(
            'SELECT COUNT(*) FROM product_data'
        )
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        return 0
    

def total_suppliers():
    conn, cursor = connect_database()
    try:
        cursor.execute(
            'SELECT COUNT(*) FROM supplier_data'
        )
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        return 0


def tax_window():
    
    def save_tax():
        saved_tax = float(tax_entry.get())
        try:
            conn, cursor = connect_database()
            if not conn or not cursor:
                return
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS tax_data(id INT PRIMARY KEY, tax DECIMAL(5,2))'
            )
            cursor.execute(
                'SELECT id FROM tax_data WHERE id=1'
            )
            if cursor.fetchone():
                cursor.execute(
                    'UPDATE tax_data SET tax=%s WHERE id=1', (saved_tax,)
                )
            else:    
                cursor.execute(
                    'INSERT INTO tax_data (id, tax) VALUES(1, %s)', (saved_tax,)
                )
            conn.commit()
            messagebox.showinfo('Success', 'Tax Saved Successfully', parent=tax_frame)
        except Exception as e:
            messagebox.showerror('Error', f'Cannot Add Tax, due to {e}')
        finally:
            conn.close()
            cursor.close()
            
    
    tax_frame = Toplevel()
    tax_frame.geometry('350x150+250+150')
    tax_frame.title('Tax Percentage')
    tax_frame.grab_set()
    
    
    tax_label = Label(tax_frame, text='Enter Tax Percentage %', font=('ariel', 12, 'bold'))
    tax_label.pack(pady=10)
    
    tax_entry = Spinbox(tax_frame, bg='lightblue', width=30, from_=0, to=100)
    tax_entry.pack(pady=10)
    
    save_button = Button(tax_frame, text='Save', font=('ariel', 12, 'bold'), bg='darkgreen', fg='white', command=lambda:save_tax())
    save_button.pack()
    


#----------main page-------#
def main_dashboard(window, full_name, user_type):

    all_employees = total_employees()
    all_products = total_products()
    all_categories = total_categories()
    all_suppliers = total_suppliers()

    dash_frame = Frame(window, height=900, width=1300)

    title_label = Label(dash_frame, text='Inventory System', font=('times new roman', 50, 'bold'), fg='white', bg='navy')
    title_label.place(x=0, y=0, relwidth=1)

    logout_button = Button(dash_frame, text='Log Out', font=('Roboto', 15, 'bold'), fg='white', bg='navy', command=lambda:logout(window))
    logout_button.place(x=1110, y=15)

    more_label = Label(dash_frame, text=f' \t\t Welcome {full_name} \t\t' , font=('Roboto', 12, 'bold'), bg='grey')
    more_label.place(x=0, y=75, relwidth=1)

    #side nav
    side_frame = Frame(dash_frame, width=200)
    side_frame.place(x=0, y=100)

    img = PhotoImage(file='images/my_logo.png')

    logo = Label(side_frame, image=img)
    logo.image = img
    logo.pack(fill=X)

    emp_button = Button(side_frame, text='Employees', font=('times new roman', 13, 'bold'), command=lambda:show_form(window, employee_form))
    emp_button.pack(fill=X)

    sup_button = Button(side_frame, text='Suppliers', font=('times new roman', 13, 'bold'), command=lambda:show_form(window, supplier_form))
    sup_button.pack(fill=X)

    cat_button = Button(side_frame, text='Category', font=('times new roman', 13, 'bold'), command=lambda:show_form(window, category_form))
    cat_button.pack(fill=X)

    products_button = Button(side_frame, text='Products', font=('times new roman', 13, 'bold'), command=lambda:show_form(window, product_form))
    products_button.pack(fill=X)

    tax_button = Button(side_frame, text='Tax', font=('times new roman', 13, 'bold'), command=lambda:tax_window())
    tax_button.pack(fill=X)

    sales_button = Button(side_frame, text='Sales', font=('times new roman', 13, 'bold'), command=lambda:show_form(window, sales_form, full_name))
    sales_button.pack(fill=X)
    
    sales_history_button = Button(
        side_frame, text='Sales History', font=('times new roman', 13, 'bold'),
        command=lambda:show_form(window, sales_history_form)
    )
    sales_history_button.pack(fill=X)

    order_button = Button(side_frame, text='My Orders', font=('times new roman', 13, 'bold'), command=lambda:show_form(window, order_form))
    order_button.pack(fill=X)

    exit_button = Button(side_frame, text='Exit', font=('times new roman', 13, 'bold'), command=lambda:exit(window))
    exit_button.pack(fill=X)
    #side bar(end)

    #Tabs

    emp_tab = Frame(dash_frame, bg='navy')
    emp_tab.place(x=400, y=150, height=150, width=200)

    emp_tab_title = Label(emp_tab, text='Total Employees', font=('Roboto', 12, 'bold'), fg='white', bg='navy')
    emp_tab_title.pack(fill=X)

    emp_tab_total = Label(emp_tab, text=f'{all_employees}', fg='white', bg='navy', font=('times new roman', 50, 'bold'))
    emp_tab_total.pack(fill=X)


    cat_tab = Frame(dash_frame, bg='saddlebrown')
    cat_tab.place(x=800, y=150, height=150, width=200)

    cat_tab_title = Label(cat_tab, text='Total Categories', font=('Roboto', 12, 'bold'), fg='white', bg='saddlebrown')
    cat_tab_title.pack(fill=X)

    cat_tab_total = Label(cat_tab, text=f'{all_categories}', fg='white', bg='saddlebrown', font=('times new roman', 50, 'bold'))
    cat_tab_total.pack(fill=X)

    supp_tab = Frame(dash_frame, bg='firebrick4')
    supp_tab.place(x=400, y=400, height=150, width=200)

    supp_tab_title = Label(supp_tab, text='Total Suppliers', font=('Roboto', 12, 'bold'), fg='white', bg='firebrick4')
    supp_tab_title.pack(fill=X)

    supp_tab_total = Label(supp_tab, text=f'{all_suppliers}', fg='white', bg='firebrick4', font=('times new roman', 50, 'bold'))
    supp_tab_total.pack(fill=X)

    products_tab = Frame(dash_frame, bg='darkgreen')
    products_tab.place(x=800, y=400, height=150, width=200)

    products_tab_title = Label(products_tab, text='Total Products', font=('Roboto', 12, 'bold'), fg='white', bg='darkgreen')
    products_tab_title.pack(fill=X)

    products_tab_total = Label(products_tab, text=f'{all_products}', fg='white', bg='darkgreen', font=('times new roman', 50, 'bold'))
    products_tab_total.pack(fill=X)

    dash_frame.pack(fill=BOTH, expand=True)
    window.protocol("WM_DELETE_WINDOW", lambda: exit(window))
    return dash_frame