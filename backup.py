import os
import shutil
import sqlite3
import threading
from datetime import datetime
from tkinter import *
from tkinter import messagebox, filedialog
from config import DB_NAME, BACKUP_DIR   # ← FIX 1: single source of truth
from database import db_lock             # ← FIX 3: shared lock


# --- Backup ---
def backup_database():
    try:
        if not os.path.exists(DB_NAME):
            return False, "Database file not found."

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")

        # FIX 3: Acquire lock so no writes happen mid-copy
        with db_lock:
            shutil.copy2(DB_NAME, backup_path)

        cleanup_old_backups()
        return True, backup_path

    except Exception as e:
        return False, str(e)


# --- Restore ---
def restore_database(backup_path):
    try:
        if not os.path.exists(backup_path):
            return False, "Backup file not found."

        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]
        conn.close()

        if result != "ok":
            return False, "Backup file is corrupted. Restore cancelled."

        with db_lock:   # ← FIX 3: lock during restore too
            shutil.copy2(backup_path, DB_NAME)

        return True, "Restore successful. Please restart the app."

    except Exception as e:
        return False, str(e)


# --- Cleanup ---
def cleanup_old_backups(limit=10):
    files = sorted(
        [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith(".db")],
        key=os.path.getmtime
    )
    for old_file in files[:-limit]:
        os.remove(old_file)


# --- Thread runner ---
def run_in_thread(window, task, on_done):
    def worker():
        result = task()
        window.after(0, lambda: on_done(result))
    threading.Thread(target=worker, daemon=True).start()


def set_buttons_state(buttons, state):
    for btn in buttons:
        btn.config(state=state)


# --- UI ---
def backup_form(window):

    def backup_action():
        try:
            set_buttons_state([backup_btn, restore_btn], DISABLED)
            backup_btn.config(text="Backing up...")

            def on_done(result):
                set_buttons_state([backup_btn, restore_btn], NORMAL)
                backup_btn.config(text="Backup My Data")
                success, msg = result
                if success:
                    messagebox.showinfo("Backup Successful", f"Saved to:\n{msg}", parent=window)
                else:
                    messagebox.showerror("Backup Failed", msg, parent=window)

            run_in_thread(window, backup_database, on_done)

        except Exception as e:
            set_buttons_state([backup_btn, restore_btn], NORMAL)
            backup_btn.config(text="Backup My Data")
            messagebox.showerror("Unexpected Error", str(e), parent=window)

    def restore_action():
        try:
            file_path = filedialog.askopenfilename(
                parent=window,                              # FIX 2: dialog stays on top
                title="Select Backup File",
                initialdir=BACKUP_DIR,
                filetypes=[("Database Files", "*.db")]
            )
            if not file_path:
                return

            confirmed = messagebox.askyesno(
                "Confirm Restore",
                "This will overwrite your current data.\nAre you sure?",
                parent=window
            )
            if not confirmed:
                return

            set_buttons_state([backup_btn, restore_btn], DISABLED)
            restore_btn.config(text="Restoring...")

            def task():
                return restore_database(file_path)

            def on_done(result):
                set_buttons_state([backup_btn, restore_btn], NORMAL)
                restore_btn.config(text="Restore My Data")
                success, msg = result
                if success:
                    messagebox.showinfo("Restore Successful", msg, parent=window)
                else:
                    messagebox.showerror("Restore Failed", msg, parent=window)

            run_in_thread(window, task, on_done)

        except Exception as e:
            set_buttons_state([backup_btn, restore_btn], NORMAL)
            restore_btn.config(text="Restore My Data")
            messagebox.showerror("Unexpected Error", str(e), parent=window)

    # --- Layout ---
    main_frame = Frame(window, width=987, height=583)
    main_frame.place(x=283, y=100)

    back = Button(
        main_frame, text='Home', font=('times new roman', 10, 'bold'), fg='white', bg='navy', command=lambda:main_frame.place_forget()
    )
    back.place(x=0, y=0)

    button_frame = Frame(main_frame, bd=1, relief=RIDGE, padx=20, pady=20)
    button_frame.place(x=300, y=200)

    Label(
        button_frame, text="Backup & Restore",
        font=("Times New Roman", 20, "bold")
    ).grid(row=0, column=0, columnspan=2, pady=(0, 15))

    Label(button_frame, text="Backup Data", font=("Times New Roman", 12)).grid(row=1, column=0, pady=10, sticky="w")
    backup_btn = Button(
        button_frame, text="Backup My Data",
        font=("Times New Roman", 12, "bold"),
        bg="#0D3B19", fg="white",
        command=backup_action
    )
    backup_btn.grid(row=1, column=1, pady=10, padx=(20, 0))

    Label(button_frame, text="Restore Data", font=("Times New Roman", 12)).grid(row=2, column=0, pady=10, sticky="w")
    restore_btn = Button(
        button_frame, text="Restore My Data",
        font=("Times New Roman", 12, "bold"),
        bg="navy", fg="white",
        command=restore_action
    )
    restore_btn.grid(row=2, column=1, pady=10, padx=(20, 0))