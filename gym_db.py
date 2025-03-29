import mysql.connector

def conectar_db(db_name=None):
    """Conecta al servidor MySQL y opcionalmente a una base de datos específica."""
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Mayo2005",
            database=db_name if db_name else None
        )
        if conexion.is_connected():
            print(f"Conexión exitosa a {'gym_db' if db_name else 'MySQL Server'}.")
            return conexion
    except mysql.connector.Error as err:
        print(f"Error al conectar: {err}")
        return None

def crear_base_de_datos():
    """Crea la base de datos gym_db si no existe."""
    conexion = conectar_db()
    if not conexion:
        return
    cursor = conexion.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS gym_db")
        print("Base de datos 'gym_db' creada o ya existe.")
    except mysql.connector.Error as err:
        print(f"Error al crear la base de datos: {err}")
    finally:
        cursor.close()
        conexion.close()

def crear_tablas():
    """Crea las tablas en la base de datos gym_db."""
    conexion = conectar_db("gym_db")
    if not conexion:
        return
    cursor = conexion.cursor()
    tablas = {
        "productos": """
        CREATE TABLE IF NOT EXISTS productos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            precio DECIMAL(10, 2) NOT NULL
        )""",
        "clientes": """
        CREATE TABLE IF NOT EXISTS clientes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            telefono VARCHAR(15),
            direccion TEXT,
            actividad VARCHAR(255),
            notas TEXT
        )""",
        "actividades": """
        CREATE TABLE IF NOT EXISTS actividades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            descripcion TEXT,
            precio DECIMAL(10, 2) DEFAULT 0,
            periodo VARCHAR(20) DEFAULT 'Mensual'
        )""",
        "inscripciones": """
        CREATE TABLE IF NOT EXISTS inscripciones (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cliente_id INT,
            actividad_id INT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
            FOREIGN KEY (actividad_id) REFERENCES actividades(id) ON DELETE CASCADE
        )""",
        "pagos": """
        CREATE TABLE IF NOT EXISTS pagos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cliente_id INT,
            actividad VARCHAR(255),
            cantidad DECIMAL(10, 2),
            fecha_pago DATE,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
        )""",
        "ingresos": """
        CREATE TABLE IF NOT EXISTS ingresos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tipo VARCHAR(255),
            cantidad DECIMAL(10, 2),
            fecha DATE
        )"""
    }
    for nombre, sql in tablas.items():
        try:
            cursor.execute(sql)
            print(f"Tabla '{nombre}' creada o ya existe.")
        except mysql.connector.Error as err:
            print(f"Error al crear la tabla {nombre}: {err}")
    cursor.close()
    conexion.close()

def actualizar_tabla_actividades():
    """Verifica si la columna 'precio' y 'periodo' existen en la tabla 'actividades' y, de no existir, las agrega."""
    conexion = conectar_db("gym_db")
    if not conexion:
        return
    cursor = conexion.cursor()
    # Verificar columna precio
    cursor.execute("SHOW COLUMNS FROM actividades LIKE 'precio'")
    result = cursor.fetchone()
    if not result:
        try:
            cursor.execute("ALTER TABLE actividades ADD COLUMN precio DECIMAL(10,2) DEFAULT 0")
            print("Columna 'precio' agregada a la tabla 'actividades'.")
        except mysql.connector.Error as err:
            print(f"Error al agregar la columna 'precio': {err}")
    else:
        print("La columna 'precio' ya existe en la tabla 'actividades'.")
    
    # Verificar columna periodo
    cursor.execute("SHOW COLUMNS FROM actividades LIKE 'periodo'")
    result = cursor.fetchone()
    if not result:
        try:
            cursor.execute("ALTER TABLE actividades ADD COLUMN periodo VARCHAR(20) DEFAULT 'Mensual'")
            print("Columna 'periodo' agregada a la tabla 'actividades'.")
        except mysql.connector.Error as err:
            print(f"Error al agregar la columna 'periodo': {err}")
    else:
        print("La columna 'periodo' ya existe en la tabla 'actividades'.")
    cursor.close()
    conexion.close()

if __name__ == "__main__":
    crear_base_de_datos()
    crear_tablas()
    actualizar_tabla_actividades()
