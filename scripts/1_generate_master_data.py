import os
import random
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine, text

load_dotenv()
fake = Faker('es_ES')
engine = create_engine(os.getenv("DATABASE_URL"))

def generate_master_data():
    with engine.connect() as conn:
        print("Iniciando inyección de datos maestros...")

        sales_persons = []
        for _ in range(20):
            code = f"VEN-{fake.unique.random_int(min=1000, max=9999)}"
            sales_persons.append(f"('{code}', '{fake.name()}', '{fake.company_email()}')")
        
        conn.execute(text(f"INSERT IGNORE INTO sales_persons (code, name, e_mail) VALUES {','.join(sales_persons)}"))
        print("Vendedores creados: 20")

        suppliers = []
        for _ in range(50):
            no = f"PROV-{fake.unique.random_int(min=10000, max=99999)}"
            suppliers.append(f"('{no}', '{fake.company().replace(chr(39), '')}', '{fake.vat_id()}')")
            
        conn.execute(text(f"INSERT IGNORE INTO suppliers (no, name, vat_registration_no) VALUES {','.join(suppliers)}"))
        print("Proveedores creados: 50")

        products = []
        categories = ['Electrónica', 'Mobiliario', 'Software', 'Servicios', 'Hardware']
        for _ in range(200):
            no = f"ART-{fake.unique.random_int(min=100000, max=999999)}"
            desc = fake.catch_phrase().replace(chr(39), '')[:50]
            price = round(random.uniform(10.0, 5000.0), 2)
            cat = random.choice(categories)
            reg_date = fake.date_between(start_date='-5y', end_date='today').isoformat()
            
            products.append(f"('{no}', '{desc}', '{cat}', {price}, 'Uds', 'ACTIVO', '{reg_date}', '{reg_date}')")
            
        conn.execute(text(f"INSERT IGNORE INTO products (no, description, item_category_code, unit_price, base_unit_of_measure, type, registration_date, last_date_modified) VALUES {','.join(products)}"))
        print("Productos creados: 200")

        customers = []
        for _ in range(500):
            no = f"CLI-{fake.unique.random_int(min=10000, max=99999)}"
            name = fake.company().replace(chr(39), '')[:50]
            city = fake.city().replace(chr(39), '')
            vat = fake.vat_id()
            customers.append(f"('{no}', '{name}', '{city}', 'ES', '{vat}', {random.randint(0, 1)})")
            
        conn.execute(text(f"INSERT IGNORE INTO customers (no, name, city, country_region_code, vat_registration_no, ordersblocked) VALUES {','.join(customers)}"))
        print("Clientes creados: 500")

        conn.commit()
        print("Proceso finalizado con éxito.")

if __name__ == "__main__":
    generate_master_data()