import streamlit as st
import mysql.connector
from datetime import datetime, timedelta
import calendar
import pandas as pd


# Función para conectar a la base de datos (ahora acepta db_name opcional)
def conectar_db(db_name="gym_db"):
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Mayo2005",
            database=db_name
        )
        if conexion.is_connected():
            return conexion
    except mysql.connector.Error as err:
        st.error(f"Error al conectar a la base de datos: {err}")
        return None

# Función para gestionar productos en el punto de venta
def conectar_db(db_name="gym_db"):
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Mayo2005",
            database=db_name
        )
        if conexion.is_connected():
            return conexion
    except mysql.connector.Error as err:
        st.error(f"Error al conectar a la base de datos: {err}")
        return None

def punto_de_venta():
    st.subheader("Punto de Venta - Gestión de Productos")
    
    # Inicializar el carrito en session_state si no existe
    if "cart" not in st.session_state:
        st.session_state.cart = []
    
    conexion = conectar_db()
    if not conexion:
        return
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, tipo, precio FROM productos")
    productos = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    if not productos:
        st.warning("No hay productos disponibles para la venta.")
        return

    # Crear diccionarios para asociar nombre con id y precio
    prod_dict = {prod[1]: prod[0] for prod in productos}
    precio_dict = {prod[1]: prod[3] for prod in productos}
    
    st.write("Lista de Productos Disponibles:")
    # Mostrar la lista en un DataFrame para mayor claridad
    df_prod = pd.DataFrame(productos, columns=["ID", "Nombre", "Tipo", "Precio"])
    st.table(df_prod)
    
    # Seleccionar producto por nombre
    producto_seleccionado = st.selectbox("Seleccione el producto a agregar", list(prod_dict.keys()))
    cantidad = st.number_input("Cantidad", min_value=1, step=1)
    
    if st.button("Agregar al Carrito"):
        id_producto = prod_dict[producto_seleccionado]
        precio_unitario = precio_dict[producto_seleccionado]
        total_item = precio_unitario * cantidad
        # Agregar al carrito (cada item es un diccionario)
        st.session_state.cart.append({
            "Producto": producto_seleccionado,
            "Cantidad": cantidad,
            "Precio Unitario": precio_unitario,
            "Total": total_item
        })
        st.success(f"Se agregó {cantidad} de {producto_seleccionado} al carrito.")
    
    # Mostrar el carrito (si existe)
    if st.session_state.cart:
        st.markdown("### Carrito de Compras")
        df_cart = pd.DataFrame(st.session_state.cart)
        total_acumulado = df_cart["Total"].sum()
        # Agregar una fila final con el total
        total_row = pd.DataFrame({
            "Producto": ["**TOTAL A PAGAR**"],
            "Cantidad": [""],
            "Precio Unitario": [""],
            "Total": [f"${total_acumulado:.2f}"]
        })
        df_cart = pd.concat([df_cart, total_row], ignore_index=True)
        st.table(df_cart)
        
        # Opción para eliminar un producto del carrito
        eliminar = st.selectbox("Seleccione un producto para eliminar del carrito", 
                                  options=[item["Producto"] for item in st.session_state.cart])
        if st.button("Eliminar del Carrito"):
            st.session_state.cart = [item for item in st.session_state.cart if item["Producto"] != eliminar]
            st.success(f"Se eliminó {eliminar} del carrito.")
        
        # Pantalla de confirmación de compra
        st.markdown("### Confirmación de Compra")
        if st.button("Confirmar Compra"):
            conexion = conectar_db()
            if not conexion:
                return
            cursor = conexion.cursor()
            # Registrar venta en ingresos (se registra el total general)
            cursor.execute("INSERT INTO ingresos (tipo, cantidad, fecha) VALUES (%s, %s, %s)",
                           ("ventas del gym", total_acumulado, datetime.now()))
            conexion.commit()
            cursor.close()
            conexion.close()
            st.success(f"Compra confirmada! Total: ${total_acumulado:.2f}")
            # Vaciar el carrito
            st.session_state.cart = []


# --- Gestión de Productos ---
def reordenar_productos():
    """
    Reordena los IDs de la tabla productos y actualiza las claves primarias.
    ADVERTENCIA: Esta práctica no es habitual, pues modificar claves primarias puede afectar la integridad referencial.
    """
    conexion = conectar_db("gym_db")
    if not conexion:
        return
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM productos ORDER BY id")
    filas = cursor.fetchall()
    mapping = {}
    new_id = 0
    for (old_id,) in filas:
        new_id += 1
        mapping[old_id] = new_id

    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    for old_id, new_id in mapping.items():
        cursor.execute("UPDATE productos SET id = %s WHERE id = %s", (new_id, old_id))
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    conexion.commit()
    cursor.close()
    conexion.close()


# Función para reordenar clientes (renumerar IDs)  
def reordenar_clientes():
    """
    Reordena los IDs de la tabla clientes y actualiza los campos foráneos en inscripciones y pagos.
    ADVERTENCIA: Esta práctica no es habitual, pues las claves primarias no deben modificarse.
    """
    conexion = conectar_db("gym_db")
    if not conexion:
        return
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id FROM clientes ORDER BY id")
    filas = cursor.fetchall()
    mapping = {}
    new_id = 0
    for (old_id,) in filas:
        new_id += 1
        mapping[old_id] = new_id
    
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    for old_id, new_id in mapping.items():
        cursor.execute("UPDATE clientes SET id = %s WHERE id = %s", (new_id, old_id))
    for old_id, new_id in mapping.items():
        cursor.execute("UPDATE inscripciones SET cliente_id = %s WHERE cliente_id = %s", (new_id, old_id))
    for old_id, new_id in mapping.items():
        cursor.execute("UPDATE pagos SET cliente_id = %s WHERE cliente_id = %s", (new_id, old_id))
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    conexion.commit()
    cursor.close()
    conexion.close()

def calcular_proximo_pago(periodo):
    hoy = datetime.now().date()
    if periodo.lower() == "semanal":
        return hoy + timedelta(days=7)
    elif periodo.lower() == "mensual":
        mes = hoy.month
        anio = hoy.year
        if mes == 12:
            mes_nuevo = 1
            anio_nuevo = anio + 1
        else:
            mes_nuevo = mes + 1
            anio_nuevo = anio
        dia = min(hoy.day, calendar.monthrange(anio_nuevo, mes_nuevo)[1])
        return datetime(anio_nuevo, mes_nuevo, dia).date()
    elif periodo.lower() == "anual":
        try:
            return hoy.replace(year=hoy.year+1)
        except ValueError:
            # Manejo para 29 de febrero
            return hoy + timedelta(days=365)
    else:
        return hoy

# Función para gestionar clientes con submenú
def gestion_clientes():
    st.subheader("Gestión de Clientes")
    opciones = ["Clientes", "Gestión de Pagos"]
    subopcion = st.selectbox("Selecciona una opción", opciones)
    
    if subopcion == "Clientes":
        # Mostrar tabla completa de clientes
        conexion = conectar_db()
        if conexion is None:
            return
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre, telefono, direccion, notas FROM clientes")
        clientes = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        if not clientes:
            st.warning("No hay clientes registrados.")
            return
        
        st.write("Lista de Clientes")
        st.table(clientes)
        
        st.markdown("### Opciones de Edición")
        accion = st.selectbox("Selecciona una acción", ["Editar Cliente", "Eliminar Cliente"])
        cliente_id = st.number_input("Ingrese el ID del cliente", min_value=1, step=1)
        
        if accion == "Editar Cliente":
            if st.button("Cargar Datos"):
                conexion = conectar_db()
                if conexion:
                    cursor = conexion.cursor()
                    cursor.execute("SELECT nombre, telefono, direccion, notas FROM clientes WHERE id = %s", (cliente_id,))
                    data = cursor.fetchone()
                    cursor.close()
                    conexion.close()
                    if data:
                        st.session_state["nombre_actual"] = data[0]
                        st.session_state["telefono_actual"] = data[1]
                        st.session_state["direccion_actual"] = data[2]
                        st.session_state["notas_actual"] = data[3]
                        conexion = conectar_db()
                        if conexion:
                            cursor = conexion.cursor()
                            cursor.execute("""
                                SELECT a.nombre 
                                FROM inscripciones i 
                                JOIN actividades a ON i.actividad_id = a.id 
                                WHERE i.cliente_id = %s
                            """, (cliente_id,))
                            inscripciones = [row[0] for row in cursor.fetchall()]
                            cursor.close()
                            conexion.close()
                            st.session_state["inscripciones_actuales"] = inscripciones
                    else:
                        st.warning("Cliente no encontrado.")
            
            nombre_def = st.session_state.get("nombre_actual", "")
            telefono_def = st.session_state.get("telefono_actual", "")
            direccion_def = st.session_state.get("direccion_actual", "")
            notas_def = st.session_state.get("notas_actual", "")
            inscripciones_def = st.session_state.get("inscripciones_actuales", [])
            
            nuevo_nombre = st.text_input("Nuevo Nombre", value=nombre_def)
            nuevo_telefono = st.text_input("Nuevo Teléfono", value=telefono_def)
            nueva_direccion = st.text_area("Nueva Dirección", value=direccion_def)
            nuevas_notas = st.text_area("Nuevas Notas", value=notas_def)
            
            conexion = conectar_db()
            if conexion:
                cursor = conexion.cursor()
                cursor.execute("SELECT nombre FROM actividades")
                actividades_list = [row[0] for row in cursor.fetchall()]
                cursor.close()
                conexion.close()
            else:
                actividades_list = []
            
            actividades_nuevas = st.multiselect("Editar Inscripciones (seleccione las actividades en las que el cliente estará inscrito)", 
                                                options=actividades_list, default=inscripciones_def)
            
            if st.button("Actualizar Cliente"):
                conexion = conectar_db()
                if conexion is None:
                    return
                cursor = conexion.cursor()
                cursor.execute(
                    "UPDATE clientes SET nombre = %s, telefono = %s, direccion = %s, notas = %s WHERE id = %s",
                    (nuevo_nombre, nuevo_telefono, nueva_direccion, nuevas_notas, cliente_id)
                )
                conexion.commit()
                cursor.close()
                cursor = conexion.cursor()
                cursor.execute("DELETE FROM inscripciones WHERE cliente_id = %s", (cliente_id,))
                conexion.commit()
                cursor.close()
                for actividad_nombre in actividades_nuevas:
                    conexion2 = conectar_db()
                    if conexion2:
                        cur = conexion2.cursor()
                        cur.execute("SELECT id FROM actividades WHERE nombre = %s", (actividad_nombre,))
                        row = cur.fetchone()
                        if row:
                            actividad_id = row[0]
                            cur.execute("INSERT INTO inscripciones (cliente_id, actividad_id) VALUES (%s, %s)", (cliente_id, actividad_id))
                            conexion2.commit()
                        cur.close()
                        conexion2.close()
                st.success("Cliente actualizado exitosamente!")
        
        elif accion == "Eliminar Cliente":
            if st.button("Eliminar Cliente"):
                conexion = conectar_db()
                if conexion is None:
                    return
                cursor = conexion.cursor()
                cursor.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
                conexion.commit()
                cursor.close()
                conexion.close()
                st.success("Cliente eliminado exitosamente!")
                reordenar_clientes()
    
    elif subopcion == "Gestión de Pagos":
        # Consultar los datos de pagos por suscripción de cada cliente
        conexion = conectar_db()
        if conexion is None:
            return
        cursor = conexion.cursor()
        query = """
        SELECT c.id, c.nombre, a.nombre, a.precio, a.periodo, p.fecha_pago, p.cantidad
        FROM inscripciones i
        JOIN clientes c ON i.cliente_id = c.id
        JOIN actividades a ON i.actividad_id = a.id
        LEFT JOIN pagos p ON c.id = p.cliente_id AND p.actividad = a.nombre
        ORDER BY c.id
        """
        cursor.execute(query)
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        # Agrupar por cliente
        data = {}
        for row in filas:
            client_id, client_name, act_nombre, act_precio, act_periodo, fecha_pago, monto = row
            if client_id not in data:
                data[client_id] = {
                    "Cliente": client_name,
                    "Actividades": [],
                    "Próxima Fecha": [],
                    "Pago a Realizar": []
                }
            # Si no hay fecha de pago, calcular la próxima fecha
            if fecha_pago is None:
                proximo = calcular_proximo_pago(act_periodo)
            else:
                proximo = fecha_pago
            # Si no se ha registrado monto, usar el precio de la actividad
            pago = monto if monto is not None else act_precio
            data[client_id]["Actividades"].append(f"• {act_nombre}")
            data[client_id]["Próxima Fecha"].append(f"• {proximo}")
            data[client_id]["Pago a Realizar"].append(f"• {pago}")
        
        # Construir lista de filas para la tabla
        tabla = []
        for client_id, info in data.items():
            fila = {
                "ID": client_id,
                "Nombre": info["Cliente"],
                "Actividades": "\n".join(info["Actividades"]),
                "Próxima Fecha": "\n".join(info["Próxima Fecha"]),
                "Pago a Realizar": "\n".join(info["Pago a Realizar"])
            }
            tabla.append(fila)
        
        if not tabla:
            st.warning("No hay pagos registrados.")
        else:
            st.write("Gestión de Pagos")
            df = pd.DataFrame(tabla)
            st.table(df)
        
        # Sección para actualizar pago
        st.markdown("### Actualizar Pago")
        cliente_id_actualizar = st.number_input("ID del Cliente", min_value=1, step=1)
        
        # Consultar las actividades a las que el cliente está inscrito, junto con precio y periodo
        conexion = conectar_db()
        if conexion is None:
            return
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT a.nombre, a.precio, a.periodo
            FROM inscripciones i
            JOIN actividades a ON i.actividad_id = a.id
            WHERE i.cliente_id = %s
        """, (cliente_id_actualizar,))
        actividades_cliente = cursor.fetchall()  # [(nombre, precio, periodo), ...]
        cursor.close()
        conexion.close()
        
        if actividades_cliente:
            opciones_actividad = [f"{row[0]} (Precio: {row[1]}, Periodo: {row[2]})" for row in actividades_cliente]
            seleccion = st.selectbox("Seleccione la actividad", opciones_actividad)
            # Extraer los datos
            try:
                actividad_actualizar = seleccion.split(" (Precio: ")[0]
                precio_actividad = float(seleccion.split(" (Precio: ")[1].split(",")[0])
                periodo = seleccion.split("Periodo: ")[1].rstrip(")")
            except Exception as e:
                st.error("Error al procesar la selección de actividad.")
                return
            
            # Utilizar el precio como monto por defecto (ya que se toma de la actividad)
            monto_pagado = st.number_input("Monto Pagado", min_value=0.0, format="%.2f", value=precio_actividad)
            # Calcular próxima fecha en función del periodo
            proximo_pago = calcular_proximo_pago(periodo)
            st.write(f"Próxima Fecha de Pago sugerida: {proximo_pago}")
            
            if st.button("Actualizar Pago"):
                conexion = conectar_db()
                if conexion is None:
                    return
                cursor = conexion.cursor()
                cursor.execute("SELECT id FROM pagos WHERE cliente_id = %s AND actividad = %s", (cliente_id_actualizar, actividad_actualizar))
                result = cursor.fetchone()
                if result:
                    pago_id = result[0]
                    cursor.execute("UPDATE pagos SET cantidad = %s, fecha_pago = %s WHERE id = %s",
                                   (monto_pagado, proximo_pago, pago_id))
                else:
                    cursor.execute("INSERT INTO pagos (cliente_id, actividad, cantidad, fecha_pago) VALUES (%s, %s, %s, %s)",
                                   (cliente_id_actualizar, actividad_actualizar, monto_pagado, proximo_pago))
                conexion.commit()
                cursor.execute("INSERT INTO ingresos (tipo, cantidad, fecha) VALUES (%s, %s, %s)",
                               ("pagos de membrecias", monto_pagado, datetime.now()))
                conexion.commit()
                cursor.close()
                conexion.close()
                st.success("Pago actualizado y registrado en ingresos!")
                
                # Mostrar alerta si hay actividades vencidas (fecha de pago pasada)
                conexion = conectar_db()
                if conexion:
                    cursor = conexion.cursor()
                    cursor.execute("""
                        SELECT a.nombre, p.fecha_pago
                        FROM pagos p
                        JOIN actividades a ON p.actividad = a.nombre
                        WHERE p.cliente_id = %s AND p.fecha_pago < %s
                    """, (cliente_id_actualizar, datetime.now().date()))
                    adeudos = cursor.fetchall()
                    cursor.close()
                    conexion.close()
                    if adeudos:
                        st.error("El cliente tiene membresías vencidas:")
                        for adeudo in adeudos:
                            st.write(f"Actividad: {adeudo[0]} - Fecha de pago: {adeudo[1]}")
        else:
            st.warning("El cliente no está inscrito en ninguna actividad.")
                
# Función para registrar clientes (con inscripción en actividades)
def registro_cliente():
    st.subheader("Registro de Nuevo Cliente")

    nombre_cliente = st.text_input("Nombre del Cliente")
    telefono_cliente = st.text_input("Teléfono del Cliente")
    direccion_cliente = st.text_area("Dirección del Cliente")
    notas_cliente = st.text_area("Notas del Cliente")

    conexion = conectar_db()
    if conexion is None:
        return
    
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, descripcion FROM actividades")
    actividades = cursor.fetchall()
    cursor.close()
    
    if actividades:
        st.write("Selecciona las actividades en las que el cliente se inscribirá:")
        actividades_seleccionadas = st.multiselect(
            "Actividades Disponibles",
            options=[actividad[1] for actividad in actividades],
            format_func=lambda x: x
        )

        if st.button("Registrar Cliente"):
            if not nombre_cliente or not telefono_cliente:
                st.warning("Por favor, ingresa el nombre y teléfono del cliente.")
                return

            conexion = conectar_db()
            if conexion is None:
                return
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO clientes (nombre, telefono, direccion, notas) VALUES (%s, %s, %s, %s)",
                           (nombre_cliente, telefono_cliente, direccion_cliente, notas_cliente))
            conexion.commit()
            cliente_id = cursor.lastrowid
            cursor.close()

            for actividad_nombre in actividades_seleccionadas:
                cursor = conexion.cursor()
                cursor.execute("SELECT id FROM actividades WHERE nombre = %s", (actividad_nombre,))
                actividad_id = cursor.fetchone()[0]
                cursor.close()
                
                cursor = conexion.cursor()
                cursor.execute("INSERT INTO inscripciones (cliente_id, actividad_id) VALUES (%s, %s)",
                               (cliente_id, actividad_id))
                conexion.commit()
                cursor.close()

            conexion.close()
            st.success("Cliente registrado exitosamente y actividades asignadas!")
    else:
        st.warning("No hay actividades registradas para asignar.")

# Función para gestionar actividades con submenú
def gestion_actividades():
    st.subheader("Gestión de Actividades")
    
    opciones = ["Ver Actividades", "Registrar Nueva Actividad", "Eliminar Actividad", "Editar Actividad"]
    subopcion = st.selectbox("Selecciona una opción", opciones)
    
    if subopcion == "Ver Actividades":
        conexion = conectar_db()
        if conexion is None:
            return
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre, descripcion, precio, periodo FROM actividades")
        actividades = cursor.fetchall()
        cursor.close()
        
        if actividades:
            for actividad in actividades:
                st.write(f"ID: {actividad[0]}, Nombre: {actividad[1]}, Descripción: {actividad[2]}, Precio: {actividad[3]}, Membresía: {actividad[4]}")
                cursor = conexion.cursor()
                cursor.execute("SELECT c.nombre FROM clientes c JOIN inscripciones i ON c.id = i.cliente_id WHERE i.actividad_id = %s", (actividad[0],))
                clientes = cursor.fetchall()
                cursor.close()
                
                if clientes:
                    st.write("Clientes inscritos:")
                    for cliente in clientes:
                        st.write(f"- {cliente[0]}")
                else:
                    st.write("No hay clientes inscritos en esta actividad.")
                st.markdown("---")
        else:
            st.warning("No hay actividades registradas.")
        conexion.close()
    
    elif subopcion == "Registrar Nueva Actividad":
        nombre_actividad = st.text_input("Nombre de la Actividad")
        descripcion_actividad = st.text_area("Descripción de la Actividad")
        precio_actividad = st.number_input("Precio de la Actividad", min_value=0.0, format="%.2f")
        periodo = st.selectbox("Tipo de Membresía", ["Semanal", "Mensual", "Anual"])
        
        if st.button("Agregar Actividad"):
            conexion = conectar_db()
            if conexion is None:
                return
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO actividades (nombre, descripcion, precio, periodo) VALUES (%s, %s, %s, %s)",
                           (nombre_actividad, descripcion_actividad, precio_actividad, periodo))
            conexion.commit()
            cursor.close()
            conexion.close()
            st.success("Actividad agregada exitosamente!")
    
    elif subopcion == "Eliminar Actividad":
        actividad_id = st.number_input("ID de la Actividad a Eliminar", min_value=1)
        
        if st.button("Eliminar Actividad"):
            conexion = conectar_db()
            if conexion is None:
                return
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM actividades WHERE id = %s", (actividad_id,))
            conexion.commit()
            cursor.close()
            conexion.close()
            st.success("Actividad eliminada exitosamente!")
    
    elif subopcion == "Editar Actividad":
        actividad_id = st.number_input("ID de la Actividad a Editar", min_value=1)
        nombre_actividad = st.text_input("Nuevo Nombre de la Actividad")
        descripcion_actividad = st.text_area("Nueva Descripción de la Actividad")
        precio_actividad = st.number_input("Nuevo Precio de la Actividad", min_value=0.0, format="%.2f")
        periodo = st.selectbox("Nuevo Tipo de Membresía", ["Semanal", "Mensual", "Anual"])
        
        if st.button("Actualizar Actividad"):
            conexion = conectar_db()
            if conexion is None:
                return
            cursor = conexion.cursor()
            cursor.execute("UPDATE actividades SET nombre = %s, descripcion = %s, precio = %s, periodo = %s WHERE id = %s",
                           (nombre_actividad, descripcion_actividad, precio_actividad, periodo, actividad_id))
            conexion.commit()
            cursor.close()
            conexion.close()
            st.success("Actividad actualizada exitosamente!")
    
# Función para gestionar ingresos
def registro_ingresos():
    st.subheader("Registro de Ingresos")
    
    # Formulario para agregar un ingreso
    with st.expander("Agregar nuevo ingreso"):
        tipo_ingreso = st.selectbox("Tipo de Ingreso", ["Actividades personalisadas", "ventas del gym", "pagos de membrecias"])
        cantidad = st.number_input("Cantidad", min_value=0.0, format="%.2f", key="nuevo_ingreso")
        if st.button("Registrar Ingreso"):
            conexion = conectar_db()
            if not conexion:
                return
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO ingresos (tipo, cantidad, fecha) VALUES (%s, %s, %s)",
                           (tipo_ingreso, cantidad, datetime.now()))
            conexion.commit()
            cursor.close()
            conexion.close()
            st.success("Ingreso registrado exitosamente!")
            # Limpiar cache de paginación al agregar un registro nuevo
            st.session_state.page = 1

    # Cargar registros de ingresos en un DataFrame
    conexion = conectar_db()
    if not conexion:
        return
    cursor = conexion.cursor()
    cursor.execute("SELECT id, tipo, cantidad, fecha FROM ingresos ORDER BY id ASC")
    registros = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    if not registros:
        st.info("No hay ingresos registrados.")
        return

    df_ingresos = pd.DataFrame(registros, columns=["ID", "Tipo", "Cantidad", "Fecha"])
    
    # Opciones para editar o eliminar registros
    st.markdown("### Editar / Eliminar Ingresos")
    col1, col2 = st.columns(2)
    with col1:
        ingreso_id = st.number_input("ID del Ingreso a editar/eliminar", min_value=1, step=1)
    with col2:
        accion = st.selectbox("Acción", ["Editar", "Eliminar"])
    
    if st.button("Ejecutar Acción"):
        conexion = conectar_db()
        if not conexion:
            return
        cursor = conexion.cursor()
        if accion == "Eliminar":
            cursor.execute("DELETE FROM ingresos WHERE id = %s", (ingreso_id,))
            conexion.commit()
            st.success(f"Ingreso con ID {ingreso_id} eliminado.")
        elif accion == "Editar":
            # Mostrar formulario de edición con valores actuales
            ingreso_sel = df_ingresos[df_ingresos["ID"] == ingreso_id]
            if ingreso_sel.empty:
                st.error("Ingreso no encontrado.")
            else:
                current_tipo = ingreso_sel.iloc[0]["Tipo"]
                current_cantidad = ingreso_sel.iloc[0]["Cantidad"]
                new_tipo = st.selectbox("Nuevo Tipo", ["Actividades personalisadas", "ventas del gym", "pagos de membrecias"], index=["Actividades personalisadas", "ventas del gym", "pagos de membrecias"].index(current_tipo))
                new_cantidad = st.number_input("Nueva Cantidad", min_value=0.0, format="%.2f", value=float(current_cantidad))
                if st.button("Confirmar Edición", key="editar_ingreso"):
                    cursor.execute("UPDATE ingresos SET tipo = %s, cantidad = %s, fecha = %s WHERE id = %s",
                                   (new_tipo, new_cantidad, datetime.now(), ingreso_id))
                    conexion.commit()
                    st.success(f"Ingreso con ID {ingreso_id} actualizado.")
        cursor.close()
        conexion.close()
        # Reiniciar la página de paginación
        st.session_state.page = 1

    # Paginación de la tabla de ingresos
    registros_por_pagina = 30
    total_registros = len(df_ingresos)
    total_paginas = (total_registros - 1) // registros_por_pagina + 1

    if "page" not in st.session_state:
        st.session_state.page = 1

    # Botones de navegación
    col_nav1, col_nav2, col_nav3 = st.columns(3)
    with col_nav1:
        if st.button("Anterior") and st.session_state.page > 1:
            st.session_state.page -= 1
    with col_nav2:
        st.write(f"Página {st.session_state.page} de {total_paginas}")
    with col_nav3:
        if st.button("Siguiente") and st.session_state.page < total_paginas:
            st.session_state.page += 1

    # Calcular los índices para la página actual
    inicio = (st.session_state.page - 1) * registros_por_pagina
    fin = inicio + registros_por_pagina
    df_paginado = df_ingresos.iloc[inicio:fin]

    st.markdown("### Lista de Ingresos")
    st.table(df_paginado)
    
# Función para gestionar productos en almacén
def gestion_productos():
    st.subheader("Almacén y Gestión de Productos")
    
    nombre_producto = st.text_input("Nombre del Producto")
    tipo_producto = st.selectbox("Tipo de Producto", ["Bebida", "Snack", "Equipo Deportivo"])
    precio_producto = st.number_input("Precio", min_value=0.0, format="%.2f")
    
    if st.button("Agregar Producto"):
        conexion = conectar_db()
        if not conexion:
            return
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO productos (nombre, tipo, precio) VALUES (%s, %s, %s)",
                       (nombre_producto, tipo_producto, precio_producto))
        conexion.commit()
        cursor.close()
        conexion.close()
        st.success("Producto agregado exitosamente!")
    
    # Opción para eliminar producto
    eliminar_producto = st.selectbox("Seleccione el producto a eliminar", options=[], key="elim_prod")
    # Para poblar el selectbox con nombres de productos, consultamos la BD
    conexion = conectar_db()
    if conexion:
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre FROM productos")
        prods = cursor.fetchall()
        cursor.close()
        conexion.close()
        if prods:
            prod_options = {nombre: prod_id for prod_id, nombre in prods}
            eliminar_producto = st.selectbox("Seleccione el producto a eliminar", list(prod_options.keys()))
            if st.button("Eliminar Producto"):
                conexion = conectar_db()
                if not conexion:
                    return
                cursor = conexion.cursor()
                prod_id = prod_options[eliminar_producto]
                cursor.execute("DELETE FROM productos WHERE id = %s", (prod_id,))
                conexion.commit()
                cursor.close()
                conexion.close()
                st.success("Producto eliminado exitosamente!")
                reordenar_productos()

    
# Función principal
def main():
    st.title("Gestión de Gimnasio 🏋️")
    menu = ["Registro de Clientes", "Punto de Venta", "Gestión de Clientes", "Gestión de Actividades", "Almacén y Gestión de Productos", "Registro de Ingresos"]
    opcion = st.sidebar.selectbox("Selecciona una opción", menu)
    
    if opcion == "Registro de Clientes":
        registro_cliente()
    elif opcion == "Punto de Venta":
        punto_de_venta()
    elif opcion == "Gestión de Clientes":
        gestion_clientes()
    elif opcion == "Gestión de Actividades":
        gestion_actividades()
    elif opcion == "Almacén y Gestión de Productos":
        gestion_productos()
    elif opcion == "Registro de Ingresos":
        registro_ingresos()

if __name__ == "__main__":
    main()
