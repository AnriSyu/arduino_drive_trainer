# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from flasgger import Swagger
import bcrypt
import pymysql
from config import MYSQL_DATABASE, MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_PORT

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "API Arduino Drive Trainer",
        "description": "Documentación personalizada para la API de Arduino Drive Trainer",
        "version": "1.0.0"
    }
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,  # all endpoints
            "model_filter": lambda tag: True,  # all models
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}


app = Flask(__name__)
CORS(app)
Swagger(app, template=swagger_template, config=swagger_config)

def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        db=MYSQL_DATABASE,
        port=MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    nickname = data.get('nickname')
    password = data.get('password')

    if not nickname or not password:
        return jsonify({"error": "Faltan datos"}), 400

    hashed_pw = hash_password(password)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nickname, password) VALUES (%s, %s)", (nickname, hashed_pw))
        conn.commit()
    except pymysql.err.IntegrityError:
        return jsonify({"error": "El nickname ya existe"}), 409
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Usuario registrado"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    nickname = data.get('nickname')
    password = data.get('password')

    if not nickname or not password:
        return jsonify({"error": "Faltan datos"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM usuarios WHERE nickname = %s", (nickname,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and check_password(password, user['password']):
        return jsonify({"message": "Login exitoso", "user_id": user['id']}), 200
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401

@app.route('/carreras', methods=['POST'])
def guardar_carrera():
    data = request.json
    usuario_id = data.get('usuario_id')
    tiempo_segundos = data.get('tiempo_segundos')
    puntaje = data.get('puntaje')
    aprobado = data.get('aprobado')
    errores = data.get('errores')
    observaciones = data.get('observaciones', '')

    if not usuario_id or tiempo_segundos is None or puntaje is None or aprobado is None or errores is None:
        return jsonify({"error": "Faltan datos para guardar la carrera"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO carreras (usuario_id, tiempo_segundos, puntaje, aprobado, errores, observaciones, fecha)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (usuario_id, tiempo_segundos, puntaje, aprobado, errores, observaciones, datetime.now())
    )
    carrera_id = cursor.lastrowid
    conn.commit()

    # Si mandas errores detallados, los guardamos en errores_carrera
    errores_detallados = data.get('errores_detallados', [])
    for err in errores_detallados:
        tipo_error = err.get('tipo_error')
        tiempo_segundo = err.get('tiempo_segundo')
        detalle = err.get('detalle', '')
        cursor.execute(
            "INSERT INTO errores_carrera (carrera_id, tipo_error, tiempo_segundo, detalle) VALUES (%s, %s, %s, %s)",
            (carrera_id, tipo_error, tiempo_segundo, detalle)
        )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Carrera guardada", "carrera_id": carrera_id}), 201

@app.route('/carreras/<int:usuario_id>', methods=['GET'])
def ver_carreras(usuario_id):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM carreras WHERE usuario_id = %s ORDER BY fecha DESC", (usuario_id,))
    carreras = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(carreras), 200

@app.route('/errores_carrera', methods=['POST'])
def guardar_errores_carrera():
    data = request.get_json()
    errores = data.get('errores', [])

    if not errores:
        return jsonify({'message': 'No se enviaron errores'}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        for error in errores:
            cursor.execute(
                "INSERT INTO errores_carrera (carrera_id, tipo_error, tiempo_segundo, detalle) VALUES (%s, %s, %s, %s)",
                (error['carrera_id'], error['tipo_error'], error['tiempo_segundo'], error['detalle'])
            )

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Errores guardados correctamente'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/errores_carrera/<int:carrera_id>', methods=['GET'])
def ver_errores_carrera(carrera_id):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM errores_carrera WHERE carrera_id = %s", (carrera_id,))
    errores = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(errores), 200


@app.route('/register', methods=['POST'])
def register_user():
    """
    Registrar un nuevo usuario
    ---
    tags:
      - Usuarios
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nickname:
              type: string
              example: juan123
            password:
              type: string
              example: mipassword
    responses:
      201:
        description: Usuario registrado
      400:
        description: Faltan datos
      409:
        description: El nickname ya existe
    """
    data = request.json
    nickname = data.get('nickname')
    password = data.get('password')

    if not nickname or not password:
        return jsonify({"error": "Faltan datos"}), 400

    hashed_pw = hash_password(password)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nickname, password) VALUES (%s, %s)", (nickname, hashed_pw))
        conn.commit()
    except pymysql.err.IntegrityError:
        return jsonify({"error": "El nickname ya existe"}), 409
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Usuario registrado"}), 201


@app.route('/login', methods=['POST'])
def login_user():
    """
    Iniciar sesión de usuario
    ---
    tags:
      - Usuarios
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nickname:
              type: string
              example: juan123
            password:
              type: string
              example: mipassword
    responses:
      200:
        description: Login exitoso
        schema:
          type: object
          properties:
            message:
              type: string
              example: Login exitoso
            user_id:
              type: integer
              example: 1
      400:
        description: Faltan datos
      401:
        description: Credenciales inválidas
    """
    data = request.json
    nickname = data.get('nickname')
    password = data.get('password')

    if not nickname or not password:
        return jsonify({"error": "Faltan datos"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM usuarios WHERE nickname = %s", (nickname,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    print(user)

    if user and check_password(password, user['password']):
        return jsonify({"message": "Login exitoso", "user_id": user['id']}), 200
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401

@app.route('/carreras', methods=['POST'])
def guardar_carrera_api():
    """
    Guardar resultados de una carrera
    ---
    tags:
      - Carreras
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            usuario_id:
              type: integer
              example: 1
            tiempo_segundos:
              type: number
              example: 95.5
            puntaje:
              type: integer
              example: 87
            aprobado:
              type: boolean
              example: true
            errores:
              type: integer
              example: 3
            observaciones:
              type: string
              example: "Buena conducción, pero falló en curva final."
            errores_detallados:
              type: array
              items:
                type: object
                properties:
                  tipo_error:
                    type: string
                    example: "Velocidad excesiva"
                  tiempo_segundo:
                    type: number
                    example: 45.2
                  detalle:
                    type: string
                    example: "Excedió límite de velocidad en zona escolar"
    responses:
      201:
        description: Carrera guardada exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
              example: Carrera guardada
            carrera_id:
              type: integer
              example: 5
      400:
        description: Faltan datos para guardar la carrera
    """
    data = request.json
    usuario_id = data.get('usuario_id')
    tiempo_segundos = data.get('tiempo_segundos')
    puntaje = data.get('puntaje')
    aprobado = data.get('aprobado')
    errores = data.get('errores')
    observaciones = data.get('observaciones', '')

    if not usuario_id or tiempo_segundos is None or puntaje is None or aprobado is None or errores is None:
        return jsonify({"error": "Faltan datos para guardar la carrera"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO carreras (usuario_id, tiempo_segundos, puntaje, aprobado, errores, observaciones, fecha)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (usuario_id, tiempo_segundos, puntaje, aprobado, errores, observaciones, datetime.now())
    )
    carrera_id = cursor.lastrowid
    conn.commit()

    errores_detallados = data.get('errores_detallados', [])
    for err in errores_detallados:
        tipo_error = err.get('tipo_error')
        tiempo_segundo = err.get('tiempo_segundo')
        detalle = err.get('detalle', '')
        cursor.execute(
            "INSERT INTO errores_carrera (carrera_id, tipo_error, tiempo_segundo, detalle) VALUES (%s, %s, %s, %s)",
            (carrera_id, tipo_error, tiempo_segundo, detalle)
        )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Carrera guardada", "carrera_id": carrera_id}), 201

@app.route('/errores_carrera', methods=['POST'])
def agregar_errores_carrera_api():
    """
    Guardar errores de carrera
    ---
    tags:
      - Errores Carrera
    parameters:
      - in: body
        name: errores
        description: Lista de errores a guardar
        required: true
        schema:
          type: object
          properties:
            errores:
              type: array
              items:
                type: object
                properties:
                  carrera_id:
                    type: integer
                    example: 1
                  tipo_error:
                    type: string
                    example: "Colisión"
                  tiempo_segundo:
                    type: number
                    example: 45.6
                  detalle:
                    type: string
                    example: "Choque con el borde de la pista"
    responses:
      201:
        description: Errores guardados correctamente
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Errores guardados correctamente"
      400:
        description: No se enviaron errores
        schema:
          type: object
          properties:
            message:
              type: string
              example: "No se enviaron errores"
      500:
        description: Error interno del servidor
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error al insertar en la base de datos"
    """
    data = request.get_json()
    errores = data.get('errores', [])

    if not errores:
        return jsonify({'message': 'No se enviaron errores'}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        for error in errores:
            cursor.execute(
                "INSERT INTO errores_carrera (carrera_id, tipo_error, tiempo_segundo, detalle) VALUES (%s, %s, %s, %s)",
                (error['carrera_id'], error['tipo_error'], error['tiempo_segundo'], error['detalle'])
            )

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Errores guardados correctamente'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/errores_carrera/<int:carrera_id>', methods=['GET'])
def obtener_errores_carrera_api(carrera_id):
    """
    Obtener errores de una carrera por ID
    ---
    tags:
      - Errores Carrera
    parameters:
      - in: path
        name: carrera_id
        type: integer
        required: true
        description: ID de la carrera para obtener sus errores
    responses:
      200:
        description: Lista de errores encontrados
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              carrera_id:
                type: integer
                example: 5
              tipo_error:
                type: string
                example: "Colisión"
              tiempo_segundo:
                type: number
                example: 42.5
              detalle:
                type: string
                example: "Choque contra el borde"
      404:
        description: No se encontraron errores para esa carrera
        schema:
          type: object
          properties:
            message:
              type: string
              example: "No se encontraron errores para la carrera"
    """
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM errores_carrera WHERE carrera_id = %s", (carrera_id,))
    errores = cursor.fetchall()
    cursor.close()
    conn.close()
    if not errores:
        return jsonify({"message": "No se encontraron errores para la carrera"}), 404
    return jsonify(errores), 200


@app.route('/carreras/<int:usuario_id>', methods=['GET'])
def obtener_carreras_por_usuario_api(usuario_id):
    """
    Obtener todas las carreras de un usuario
    ---
    tags:
      - Carreras
    parameters:
      - in: path
        name: usuario_id
        type: integer
        required: true
        description: ID del usuario
        example: 1
    responses:
      200:
        description: Lista de carreras del usuario ordenadas por fecha descendente
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 10
              usuario_id:
                type: integer
                example: 1
              fecha:
                type: string
                format: date-time
                example: '2025-05-27T21:00:00'
              tiempo_segundos:
                type: number
                example: 92.3
              puntaje:
                type: integer
                example: 89
              aprobado:
                type: boolean
                example: true
              errores:
                type: integer
                example: 2
              observaciones:
                type: string
                example: "Muy buena carrera"
      404:
        description: Usuario no encontrado o sin carreras
    """
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM carreras WHERE usuario_id = %s ORDER BY fecha DESC", (usuario_id,))
    carreras = cursor.fetchall()
    cursor.close()
    conn.close()

    if not carreras:
        return jsonify({"message": "No se encontraron carreras para este usuario"}), 404

    return jsonify(carreras), 200

if __name__ == '__main__':
    app.run(debug=True,port=8000)
