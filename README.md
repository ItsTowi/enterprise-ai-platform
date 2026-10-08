# Enterprise AI Platform

Plataforma empresarial impulsada por IA. Permite hacer preguntas en lenguaje natural sobre un ERP (modelo de datos inspirado en Microsoft Dynamics 365 Business Central) y obtener la respuesta con datos reales de la base de datos.

> Proyecto de aprendizaje: cada pieza se construye y se entiende por separado antes de pasar a la siguiente.

## Estado del proyecto

| Fase | Pieza | Estado |
|---|---|---|
| 1 | MySQL 8.0 en Docker, 12 tablas estilo Business Central | Hecho |
| 1 | Datos de prueba: 500 clientes, 200 productos, 50 proveedores, 20 vendedores, 1.000 facturas | Hecho |
| 1 | 50 contratos PDF ligados a clientes (para el futuro RAG) | Hecho |
| 2B | Conexión de solo lectura, configuración, inspector de esquema | Hecho |
| 2B | Validador de SQL (AST con `sqlglot`) con tests | Hecho |
| 2B | Cliente LLM, prompt y orquestador Text-to-SQL con autocorrección | Hecho |
| 2B | API REST con FastAPI (`POST /v1/query`) | Pendiente |
| 2B | Datos coherentes + conjunto de evaluación | Pendiente |
| 2A | Motor RAG sobre los contratos PDF | Pendiente |
| 3 | Router SQL / RAG, logging, autenticación, Docker Compose completo | Pendiente |

## Cómo funciona (Text-to-SQL)

```
Pregunta -> Prompt (esquema + reglas) -> LLM -> Validador de SQL -> MySQL (solo lectura) -> Resultado
                                          ^                |
                                          +-- error + 1 reintento
```

El LLM no tiene acceso a la base de datos: solo escribe texto (una consulta SQL). Quien decide si se ejecuta es el código del proyecto.

1. **Prompt** (`app/llm/prompts.py`): rol, esquema de las tablas (`describe_schema`), relaciones entre tablas, reglas de dialecto MySQL y formato de salida JSON.
2. **LLM** (`app/llm/client.py`): OpenAI con temperatura 0 y salida JSON. Responde `{"sql": "...", "reason": null}`, o `{"sql": null, "reason": "..."}` si la pregunta no se puede responder con los datos (vía de escape para que no invente consultas).
3. **Validador** (`app/services/sql_validator.py`): parsea el SQL a un árbol (AST) y lo comprueba antes de ejecutarlo.
4. **Ejecución** (`app/db/session.py`): engine de SQLAlchemy con un usuario MySQL de solo lectura y un límite de 5 segundos por consulta.
5. **Orquestador** (`app/services/text_to_sql.py`): une todo. Si el validador o MySQL rechazan la consulta, se la devuelve al LLM con el error para que la corrija (un solo reintento).

### Capas de seguridad

El SQL generado por un LLM es una entrada no confiable. Se protege en varias capas independientes:

| Capa | Dónde | Qué impide |
|---|---|---|
| Usuario `ai_readonly` | MySQL | Cualquier `INSERT`, `UPDATE`, `DELETE` o `DROP` (error 1142), aunque falle todo lo demás |
| Una sola sentencia | Validador | `SELECT 1; DROP TABLE x` |
| Solo lectura | Validador | Cualquier cosa que no sea `SELECT`/`UNION`/`INTERSECT`/`EXCEPT` |
| Lista blanca de tablas | Validador | `mysql.user`, `information_schema`, nombres con esquema (`db.tabla`) |
| Construcciones y funciones prohibidas | Validador | `INTO OUTFILE`, `FOR UPDATE`, `SLEEP`, `BENCHMARK`, `LOAD_FILE`, `GET_LOCK` |
| `LIMIT` forzado (máx. 100) | Validador | Respuestas gigantes |
| `max_execution_time` = 5 s | Engine | Consultas lentas (aplica a `SELECT`) |

Lo que se ejecuta es siempre el SQL regenerado desde el AST ya validado, nunca el texto original del modelo.

## 🛠 Tecnologías

* **Infraestructura:** Docker, MySQL 8.0
* **Datos:** Python 3.13, SQLAlchemy, Faker, FPDF2
* **IA / Backend:** OpenAI API (`gpt-4o-mini`), `sqlglot`, `pydantic-settings`
* **Tests:** pytest
* **Entorno:** `venv`, secretos en `.env`

## Estructura del proyecto

```
enterprise-ai-platform/
├── app/
│   ├── core/config.py            # Configuración (lee .env, tipada con pydantic-settings)
│   ├── db/
│   │   ├── session.py            # get_engine(): engine de solo lectura con pool y timeout
│   │   └── schema_inspector.py   # describe_schema(): esquema + relaciones como texto
│   ├── llm/
│   │   ├── prompts.py            # System prompt y mensaje de reintento
│   │   └── client.py             # generate_sql(): llamada a OpenAI
│   ├── services/
│   │   ├── sql_validator.py      # validate_sql(): seguridad sobre el AST
│   │   └── text_to_sql.py        # answer_question(): flujo completo
│   └── utils/exceptions.py       # InvalidSQLException, LLMResponseError, TextToSqlError
├── scripts/
│   ├── 1_generate_master_data.py # Datos maestros
│   ├── 2_generate_transactions.py# Facturas
│   ├── 3_generate_pdfs.py        # Contratos PDF
│   ├── ask.py                    # Hacer una pregunta desde terminal
│   └── check_*.py                # Comprobaciones manuales (conexión, prompt, LLM)
├── tests/unit/                   # Tests del validador y del orquestador
├── database/schema.sql           # DDL de las 12 tablas
├── docs/contracts/               # PDFs generados (no versionados)
├── docker-compose.yml
└── requirements.txt
```

## 🚀 Guía de instalación y uso

### 1. Requisitos previos

* Docker (o OrbStack) instalado y ejecutándose.
* Python 3.13 o superior.
* Una clave de API de OpenAI.

### 2. Entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y rellena la clave de OpenAI y la contraseña del usuario de solo lectura. `.env` está en `.gitignore`; no lo subas nunca al repositorio.

### 4. Base de datos y datos de prueba

```bash
docker compose up -d
python scripts/1_generate_master_data.py
python scripts/2_generate_transactions.py
python scripts/3_generate_pdfs.py
```

El contenedor (`erp_mysql`) crea las tablas automáticamente la primera vez, desde `database/schema.sql`.

### 5. Usuario de solo lectura (una sola vez)

```bash
docker exec -it erp_mysql mysql -u root -p
```

```sql
CREATE USER 'ai_readonly'@'%' IDENTIFIED BY 'la_misma_password_que_en_.env';
GRANT SELECT ON middleware.* TO 'ai_readonly'@'%';
SHOW GRANTS FOR 'ai_readonly'@'%';
```

### 6. Hacer una pregunta

Desde la raíz del proyecto:

```bash
python -m scripts.ask "¿Cuántos clientes hay?"
python -m scripts.ask "Top 5 clientes por importe facturado"
python -m scripts.ask "¿Cuántos pedidos hay pendientes?"
```

Imprime el SQL ejecutado, el número de filas y las 10 primeras. Si la pregunta no se puede responder con los datos, imprime `Sin consulta: <motivo>`.

### 7. Tests

```bash
python -m pytest tests/unit -v
```

Los tests no necesitan MySQL ni OpenAI: el orquestador se prueba con un LLM y una base de datos simulados.

> **Importante:** ejecuta siempre los módulos de `app/` con `python -m ...` desde la raíz del proyecto (por ejemplo `python -m scripts.ask`). Ejecutar `python app/db/session.py` falla con `ModuleNotFoundError: No module named 'app'`, porque Python solo ve la carpeta del archivo y no la raíz. Los scripts de generación de datos (`1_`, `2_`, `3_`) sí se ejecutan directamente.

## Limitaciones conocidas

* **Datos de prueba incoherentes con Business Central.** Las facturas se generaron sin stock previo ni movimientos contables: `item_ledger_entries` y `cust_ledger_entries` no reflejan las ventas, y `products.inventory` o `customers.balance_lcy` no cuadran con ellos. Hay que regenerar los datos con esas invariantes antes de evaluar con rigor.
* **Solo hay datos de facturas.** Las tablas de pedidos y compras existen pero están vacías.
* **El esquema es grande** (más de 700 líneas, sobre todo `products` y `customers`) y se envía completo en cada petición. Recortarlo reduciría coste y mejoraría la precisión.
* **Las relaciones entre tablas se declaran a mano** (`RELATIONSHIPS` en `schema_inspector.py`): la base de datos no define claves foráneas, solo códigos de negocio.
* **El prompt describe el estado de los datos** (solo facturas, líneas de tipo artículo). Debe actualizarse cuando cambien.

## Próximos pasos

1. API con FastAPI: `POST /v1/query`, modelos Pydantic, errores HTTP correctos y serialización de `Decimal` y fechas.
2. Regenerar los datos con coherencia contable y un script que verifique las invariantes.
3. Conjunto de evaluación (20-30 preguntas con SQL de referencia, comparando resultados ejecutados).
4. Motor RAG sobre los contratos PDF.
5. Router que decida entre SQL, RAG o ambos.
