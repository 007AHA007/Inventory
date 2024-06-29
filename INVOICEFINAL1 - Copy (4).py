import os
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
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

# Log order in inventory_updates table
def log_order(product_id, old_quantity, new_quantity):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO inventory_updates (product_id, old_quantity, new_quantity, update_type, update_time)
    VALUES (%s, %s, %s, 'Order', %s)
    """, (product_id, old_quantity, new_quantity, datetime.now()))
    conn.commit()
    conn.close()

class InvoiceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Invoice Generator")
        self.setGeometry(100, 100, 600, 400)

        self.layout = QVBoxLayout()

        self.label_name = QLabel("Customer Name:")
        self.input_name = QLineEdit()

        self.label_address = QLabel("Address:")
        self.input_address = QLineEdit()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Product ID", "Quantity", "Price"])

        self.button_add_product = QPushButton("Add Product")
        self.button_add_product.clicked.connect(self.add_product)

        self.button_generate = QPushButton("Generate Invoice")
        self.button_generate.clicked.connect(self.generate_invoice)

        self.layout.addWidget(self.label_name)
        self.layout.addWidget(self.input_name)
        self.layout.addWidget(self.label_address)
        self.layout.addWidget(self.input_address)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.button_add_product)
        self.layout.addWidget(self.button_generate)

        self.setLayout(self.layout)

    def add_product(self):
        product_id, ok = QInputDialog.getText(self, 'Product ID', 'Enter Product ID:')
        if not ok:
            return

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory WHERE product_id=%s", (product_id,))
            result = cursor.fetchone()

            if result:
                # Product exists, check quantity
                quantity = self.get_product_quantity(product_id)
                if quantity == -1:
                    QMessageBox.warning(self, "Database Error", "Error fetching quantity from database")
                    return
                elif quantity == 0:
                    QMessageBox.warning(self, "Insufficient Quantity", "Product quantity is insufficient")
                    return
                else:
                    self.add_product_to_table(product_id, quantity)
            else:
                QMessageBox.warning(self, "Invalid Product ID", "Product ID not found")
                return
        except Exception as e:
            QMessageBox.warning(self, "Database Error", str(e))
            return

    def get_product_quantity(self, product_id):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT quantity FROM inventory WHERE product_id=%s", (product_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0]
            else:
                return -1  # Product ID not found
        except Exception as e:
            print("Error fetching quantity:", e)
            return -1

    def add_product_to_table(self, product_id, quantity):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.table.setItem(row_count, 0, QTableWidgetItem(product_id))
        self.table.setItem(row_count, 1, QTableWidgetItem(str(quantity)))
        self.table.setItem(row_count, 2, QTableWidgetItem(""))  # Placeholder for price

    def validate_inputs(self):
        customer_name = self.input_name.text()
        customer_address = self.input_address.text()

        if not customer_name or not customer_address:
            QMessageBox.warning(self, "Input Error", "Customer name and address are required")
            return False

        return True

    def generate_invoice(self):
        if not self.validate_inputs():
            return

        customer_name = self.input_name.text()
        customer_address = self.input_address.text()

        # Generate invoice using ReportLab
        self.generate_pdf_invoice(customer_name, customer_address)

    def generate_pdf_invoice(self, customer_name, customer_address):
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        pdf_file_name = f"{date_time}_{customer_name}_{customer_address}_invoice.pdf"
        downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
        pdf_file_path = os.path.join(downloads_folder, pdf_file_name)
        c = canvas.Canvas(pdf_file_path, pagesize=letter)

        # Set font and size
        c.setFont("Helvetica-Bold", 12)

        # Invoice Header
        c.drawString(100, 750, "INVOICE")
        c.setFont("Helvetica", 10)
        c.drawString(100, 730, f"Customer Name: {customer_name}")
        c.drawString(100, 710, f"Address: {customer_address}")
        c.drawString(100, 690, f"Date: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        c.line(50, 700, 550, 700)  # Horizontal line

        # Table Header
        table_y = 680
        c.drawString(100, table_y, "Product ID")
        c.drawString(250, table_y, "Quantity")
        c.drawString(350, table_y, "Price")
        c.line(50, table_y - 10, 550, table_y - 10)  # Horizontal line

        # Table Content
        total_amount = 0
        for row_index in range(self.table.rowCount()):
            product_id = self.table.item(row_index, 0).text()
            quantity = int(self.table.item(row_index, 1).text())
            price = float(self.table.item(row_index, 2).text())
            total_amount += quantity * price

            table_y -= 20
            c.drawString(100, table_y, product_id)
            c.drawString(250, table_y, str(quantity))
            c.drawString(350, table_y, f"${price:.2f}")

            # Update inventory quantity and log order
            update_inventory(product_id, quantity)

        # Total Amount
        c.line(50, table_y - 20, 550, table_y - 20)  # Horizontal line
        c.drawString(250, table_y - 30, "Total:")
        c.drawString(350, table_y - 30, f"${total_amount:.2f}")

        # Footer
        c.line(50, 50, 550, 50)  # Horizontal line
        c.setFont("Helvetica-Bold", 10)
        c.drawString(100, 30, "NMT")
        c.setFont("Helvetica", 8)
        c.drawString(400, 30, "Powered by ATM")

        c.save()
        QMessageBox.information(self, "Success", f"Invoice generated successfully! Saved as {pdf_file_path}")

def update_inventory(product_id, quantity):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Get the current quantity from the database
        cursor.execute("SELECT quantity FROM inventory WHERE product_id=%s", (product_id,))
        result = cursor.fetchone()

        if result:
            old_quantity = result[0]
            new_quantity = old_quantity - quantity

            if new_quantity >= 0:
                # Update the inventory table with the new quantity
                cursor.execute("UPDATE inventory SET quantity=%s WHERE product_id=%s",
                               (new_quantity, product_id))

                # Log the order in the inventory_updates table
                log_order(product_id, old_quantity, new_quantity)

                conn.commit()
            else:
                print("Insufficient quantity in inventory.")
        else:
            print("Product ID not found in inventory.")

        conn.close()
    except Exception as e:
        print("Error updating inventory:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InvoiceApp()
    window.show()
    sys.exit(app.exec())
