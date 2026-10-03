import os
import random
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from fpdf import FPDF
from fpdf.enums import XPos, YPos

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
PDF_DIR = "docs/contracts"

os.makedirs(PDF_DIR, exist_ok=True)

class ContractPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'CONTRATO DE PRESTACIÓN DE SERVICIOS', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')

def generate_pdfs():
    servicios_opts = [
        "mantenimiento de infraestructura Cloud y consultoría DevOps",
        "migración de datos estructurados e implementación de Microsoft Dynamics 365",
        "despliegue de modelos de Machine Learning y auditoría de ciberseguridad",
        "soporte técnico nivel 3 y administración de bases de datos relacionales"
    ]
    sla_opts = ["99.9%", "99.95%", "98.5%", "99.0%"]
    duracion_opts = ["12 meses", "24 meses", "36 meses", "indefinida con revisión anual"]
    penalizacion_opts = [
        "Cualquier impago superior a 60 días facultará al proveedor para la rescisión unilateral del servicio.",
        "El retraso en el pago conllevará un recargo del 5% mensual sobre la cantidad adeudada.",
        "Si el cliente incumple las cuotas durante 2 meses consecutivos, se procederá al bloqueo de la cuenta y acciones legales.",
        "Las partes acuerdan un periodo de gracia de 15 días, tras el cual se suspenderán los servicios de forma cautelar."
    ]

    with engine.connect() as conn:
        print("Generando contratos PDF...")
        customers = conn.execute(text("SELECT no, name, city, vat_registration_no FROM customers LIMIT 50")).fetchall()

        for no, name, city, vat in customers:
            pdf = ContractPDF()
            pdf.add_page()
            pdf.set_font('Helvetica', '', 11)
            
            fecha = datetime.now().strftime("%d/%m/%Y")
            
            servicio = random.choice(servicios_opts)
            sla = random.choice(sla_opts)
            duracion = random.choice(duracion_opts)
            penalizacion = random.choice(penalizacion_opts)
            
            texto = f"""
En la ciudad de {city}, a {fecha}.

REUNIDOS:
De una parte, ENTERPRISE AI PLATFORM, con sede central en Madrid y NIF B-12345678.
De otra parte, {name}, con identificador de cliente {no} y NIF {vat} (en adelante, el CLIENTE).

ACUERDAN:
1. OBJETO DEL CONTRATO: 
El proveedor se compromete a suministrar al CLIENTE los servicios de {servicio}, garantizando un SLA (Service Level Agreement) del {sla}.

2. CONFIDENCIALIDAD Y PROTECCIÓN DE DATOS:
Ambas partes se comprometen a mantener el más estricto secreto profesional respecto a la información técnica y comercial cruzada durante la vigencia de este acuerdo, cumpliendo íntegramente con el RGPD y la normativa europea de protección de datos.

3. DURACIÓN Y RESOLUCIÓN:
Este contrato tiene una duración de {duracion}. {penalizacion}

4. JURISDICCIÓN:
Las partes se someten expresamente a los juzgados y tribunales de {city} para la resolución de cualquier controversia derivada del presente acuerdo, renunciando a cualquier otro fuero que pudiera corresponderles.
"""
            
            pdf.multi_cell(0, 8, texto.strip())
            pdf.output(f"{PDF_DIR}/Contrato_{no}.pdf")
            
        print(f"Proceso finalizado: {len(customers)} contratos PDF generados en {PDF_DIR}/.")

if __name__ == "__main__":
    generate_pdfs()