import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
from datetime import datetime

# Database connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="tiger",
        database="service"
    )

# Initialize database
def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        product_id VARCHAR(255) PRIMARY KEY,
        item_name VARCHAR(255) NOT NULL,
        quantity INT NOT NULL,
        box_id VARCHAR(255) -- Add this column for box ID
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_updates (
        update_id INT AUTO_INCREMENT PRIMARY KEY,
        product_id VARCHAR(255),
        item_name VARCHAR(255),
        old_quantity INT,
        new_quantity INT,
        update_type VARCHAR(255),
        update_time DATETIME
    )
    """)
    conn.close()

# Log updates to inventory_updates table
def log_update(product_id, item_name, old_quantity, new_quantity, update_type):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO inventory_updates (product_id, item_name, old_quantity, new_quantity, update_type, update_time)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, (product_id, item_name, old_quantity, new_quantity, update_type, datetime.now()))
    conn.commit()
    conn.close()

# Add item to inventory
def add_item():
    product_id = product_id_var.get()
    item_name = item_name_var.get()
    quantity = quantity_var.get()
    box_id = box_id_var.get()

    if not product_id or not item_name or not quantity or not box_id:
        messagebox.showerror("Input Error", "All fields are required")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM inventory WHERE product_id=%s", (product_id,))
        result = cursor.fetchone()

        if result:
            old_quantity = result[0]
            new_quantity = old_quantity + quantity
            cursor.execute("UPDATE inventory SET quantity=%s, box_id=%s WHERE product_id=%s",
                           (new_quantity, box_id, product_id))
            log_update(product_id, item_name, old_quantity, new_quantity, "Add")
        else:
            cursor.execute("INSERT INTO inventory (product_id, item_name, quantity, box_id) VALUES (%s, %s, %s, %s)",
                           (product_id, item_name, quantity, box_id))
            log_update(product_id, item_name, 0, quantity, "Add")

        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Inventory updated successfully")
        fetch_items()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))

# Fetch items from inventory
def fetch_items():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory")
        rows = cursor.fetchall()
        conn.close()

        for row in inventory_list.get_children():
            inventory_list.delete(row)

        for row in rows:
            inventory_list.insert("", "end", values=row)
    except Exception as e:
        messagebox.showerror("Database Error", str(e))

# Search item by product ID
def search_item():
    product_id = product_id_var.get()

    if not product_id:
        messagebox.showerror("Input Error", "Product ID is required")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory WHERE product_id=%s", (product_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            messagebox.showinfo("Search Result", f"Product ID: {row[0]}\nItem Name: {row[1]}\nQuantity: {row[2]}\nBox ID: {row[3]}")
        else:
            messagebox.showinfo("Search Result", "No item found with that Product ID")
    except Exception as e:
        messagebox.showerror("Database Error", str(e))

# GUI Setup
root = ctk.CTk()
root.title("Inventory Management System")
root.geometry("800x600")

form_frame = ctk.CTkFrame(root)
form_frame.pack(pady=20)

ctk.CTkLabel(form_frame, text="Product ID:", font=("Arial", 14)).grid(row=0, column=0, padx=10, pady=5)
ctk.CTkLabel(form_frame, text="Item Name:", font=("Arial", 14)).grid(row=1, column=0, padx=10, pady=5)
ctk.CTkLabel(form_frame, text="Quantity:", font=("Arial", 14)).grid(row=2, column=0, padx=10, pady=5)
ctk.CTkLabel(form_frame, text="Box ID:", font=("Arial", 14)).grid(row=3, column=0, padx=10, pady=5)

product_id_var = tk.StringVar()
item_name_var = tk.StringVar()
quantity_var = tk.IntVar()
box_id_var = tk.StringVar()

product_id_entry = ctk.CTkEntry(form_frame, textvariable=product_id_var, font=("Arial", 14))
product_id_entry.grid(row=0, column=1, padx=10, pady=5)
item_name_entry = ctk.CTkEntry(form_frame, textvariable=item_name_var, font=("Arial", 14))
item_name_entry.grid(row=1, column=1, padx=10, pady=5)
quantity_entry = ctk.CTkEntry(form_frame, textvariable=quantity_var, font=("Arial", 14))
quantity_entry.grid(row=2, column=1, padx=10, pady=5)
box_id_entry = ctk.CTkEntry(form_frame, textvariable=box_id_var, font=("Arial", 14))
box_id_entry.grid(row=3, column=1, padx=10, pady=5)

ctk.CTkButton(form_frame, text="Add Item", command=add_item).grid(row=4, column=0, columnspan=2, pady=10)
ctk.CTkButton(form_frame, text="Search Item", command=search_item).grid(row=5, column=0, columnspan=2, pady=10)

inventory_list_frame = ctk.CTkFrame(root)
inventory_list_frame.pack(pady=20)

inventory_list = ttk.Treeview(inventory_list_frame, columns=("Product ID", "Item Name", "Quantity", "Box ID"), show='headings')
inventory_list.heading("Product ID", text="Product ID")
inventory_list.heading("Item Name", text="Item Name")
inventory_list.heading("Quantity", text="Quantity")
inventory_list.heading("Box ID", text="Box ID")
inventory_list.pack(fill=tk.BOTH, expand=1)

fetch_items()

root.mainloop()
