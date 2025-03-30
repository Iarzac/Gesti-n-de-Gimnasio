import sqlite3

def conectar_db(db_name="gym_db.db"):
    """Conecta a la base de datos SQLite (creando una nueva si no existe)."""
    try:
        conexion = sqlite3.connect(db_name)
        print(f"Conexión exitosa a la base de datos {db_name}.")
        return conexion
    except sqlite3.Error as err:
        print(f"Error al conectar: {err}")
        return None

def crear_base_de_datos():
    """Crea la base de datos gym_db.db si no existe (en SQLite no es necesario explícitamente)."""
    conexion = conectar_db()
    if not conexion:
        return
    conexion.close()

def crear_tablas():
    """Crea las tablas en la base de datos gym_db.db."""
    conexion = conectar_db("gym_db.db")
    if not conexion:
        return
    cursor = conexion.cursor()
    tablas = {
        "productos": """
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            precio REAL NOT NULL
        )""",
        "clientes": """
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            actividad TEXT,
            notas TEXT
        )""",
        "actividades": """
        CREATE TABLE IF NOT EXISTS actividades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL DEFAULT 0,
            periodo TEXT DEFAULT 'Mensual'
        )""",
        "inscripciones": """
        CREATE TABLE IF NOT EXISTS inscripciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            actividad_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
            FOREIGN KEY (actividad_id) REFERENCES actividades(id) ON DELETE CASCADE
        )""",
        "pagos": """
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            actividad TEXT,
            cantidad REAL,
            fecha_pago TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
        )""",
        "ingresos": """
        CREATE TABLE IF NOT EXISTS ingresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            cantidad REAL,
            fecha TEXT
        )"""
    }
    for nombre, sql in tablas.items():
        try:
            cursor.execute(sql)
            print(f"Tabla '{nombre}' creada o ya existe.")
        except sqlite3.Error as err:
            print(f"Error al crear la tabla {nombre}: {err}")
    cursor.close()
    conexion.close()

def actualizar_tabla_actividades():
    """Verifica si la columna 'precio' y 'periodo' existen en la tabla 'actividades' y, de no existir, las agrega."""
    conexion = conectar_db("gym_db.db")
    if not conexion:
        return
    cursor = conexion.cursor()
    
    # No necesitamos verificar las columnas como en MySQL, ya que SQLite no soporta `SHOW COLUMNS`.
    # Si ya definimos estas columnas al crear la tabla, no es necesario hacer la verificación.
    try:
        cursor.execute("ALTER TABLE actividades ADD COLUMN precio REAL DEFAULT 0")
        print("Columna 'precio' agregada a la tabla 'actividades'.")
    except sqlite3.OperationalError:
        print("La columna 'precio' ya existe en la tabla 'actividades'.")

    try:
        cursor.execute("ALTER TABLE actividades ADD COLUMN periodo TEXT DEFAULT 'Mensual'")
        print("Columna 'periodo' agregada a la tabla 'actividades'.")
    except sqlite3.OperationalError:
        print("La columna 'periodo' ya existe en la tabla 'actividades'.")
    
    cursor.close()
    conexion.close()

if __name__ == "__main__":
    crear_base_de_datos()
    crear_tablas()
    actualizar_tabla_actividades()
