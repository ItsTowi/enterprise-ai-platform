from sqlalchemy import Engine, inspect

RELATIONSHIPS: list[tuple[str, str]] = [
    ("sales_invoice_headers.sell_to_customer_no", "customers.no"),
    ("sales_invoice_lines.document_no", "sales_invoice_headers.no"),
    ("sales_invoice_lines.no", "products.no"),
    ("sales_order_headers.sell_to_customer_no", "customers.no"),
    ("sales_order_lines.document_no", "sales_order_headers.no"),
    ("purchase_order_headers.buy_from_vendor_no", "suppliers.no"),
    ("purchase_order_lines.document_no", "purchase_order_headers.no"),
    ("cust_ledger_entries.customer_no", "customers.no"),
    ("item_ledger_entries.item_no", "products.no"),
    ("customers.salesperson_code", "sales_persons.code"),
]


def describe_schema(engine: Engine) -> str:
    inspector = inspect(engine)
    lines: list[str] = []

    for table in inspector.get_table_names():
        lines.append(f"Tabla: {table}")
        for column in inspector.get_columns(table):
            lines.append(f"  - {column['name']} ({str(column['type']).split(" COLLATE")[0]})")

    lines.append("")
    lines.append("Relaciones:")
    for source, target in RELATIONSHIPS:
        lines.append(f"  {source} -> {target}")

    return "\n".join(lines)