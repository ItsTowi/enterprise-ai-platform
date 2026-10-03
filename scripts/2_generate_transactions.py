import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

def generate_transactions():
    with engine.connect() as conn:
        print("Obteniendo datos maestros...")
        
        customers = [row[0] for row in conn.execute(text("SELECT no FROM customers")).fetchall()]
        sales_persons = [row[0] for row in conn.execute(text("SELECT code FROM sales_persons")).fetchall()]
        
        products_data = conn.execute(text("SELECT no, unit_price FROM products")).fetchall()
        products = {row[0]: float(row[1]) for row in products_data}
        product_ids = list(products.keys())

        if not customers or not products or not sales_persons:
            print("Error: Faltan datos maestros. Ejecutar el script 1 primero.")
            return

        print("Generando 1000 facturas de venta...")
        
        invoice_headers = []
        invoice_lines = []
        
        for i in range(1, 1001):
            inv_no = f"FV-26-{str(i).zfill(5)}"
            customer_no = random.choice(customers)
            salesperson_code = random.choice(sales_persons)
            
            days_ago = random.randint(0, 730)
            posting_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            total_amount = 0
            num_lines = random.randint(1, 5)
            
            for line_no in range(1, num_lines + 1):
                item_no = random.choice(product_ids)
                unit_price = products[item_no]
                qty = random.randint(1, 20)
                line_amount = unit_price * qty
                total_amount += line_amount
                
                invoice_lines.append(f"('{inv_no}', {line_no * 1000}, '{customer_no}', '{item_no}', {qty}, {unit_price}, {line_amount})")

            invoice_headers.append(f"('{inv_no}', 'PED-0000', '{customer_no}', '{posting_date}', '{salesperson_code}', {total_amount}, 0, 0, 0, 0, 0, 0)")

        print("Inyectando cabeceras en base de datos...")
        chunk_size = 250
        for i in range(0, len(invoice_headers), chunk_size):
            chunk = invoice_headers[i:i + chunk_size]
            conn.execute(text(f"""
                INSERT IGNORE INTO sales_invoice_headers 
                (no, order_no, sell_to_customer_no, posting_date, salesperson_code, amount, vat_base_discount_percent, remaining_amount, invoice_discount_amount, document_freight, merch_points, gift_percentage) 
                VALUES {','.join(chunk)}
            """))

        print("Inyectando líneas de detalle en base de datos...")
        for i in range(0, len(invoice_lines), chunk_size):
            chunk = invoice_lines[i:i + chunk_size]
            conn.execute(text(f"""
                INSERT IGNORE INTO sales_invoice_lines 
                (document_no, line_no, sell_to_customer_no, no, quantity, unit_price, amount) 
                VALUES {','.join(chunk)}
            """))

        conn.commit()
        print(f"Proceso finalizado: 1000 facturas y {len(invoice_lines)} líneas inyectadas.")

if __name__ == "__main__":
    generate_transactions()