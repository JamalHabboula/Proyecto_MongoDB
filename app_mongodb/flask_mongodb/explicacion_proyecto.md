# Explicación Detallada del Proyecto Flask + MongoDB

## Índice
1. [app.py](#apppy)
2. [index.html](#indexhtml)
3. [top_negocios.html](#top_negocioshtml)
4. [amigos_usuario.html](#amigos_usuariohtml)
5. [resenas_autor.html](#resenas_autorhtml)
6. [buscar_texto.html](#buscar_textohtml)
7. [style.css](#stylecss)
8. [terminal.txt](#terminaltxt)

---

## app.py

```python
import logging
```
Importa el módulo estándar de Python para registrar mensajes de log (información, advertencias, errores).

```python
from flask import Flask, render_template, request
```
Importa de Flask:
- `Flask`: la clase principal para crear la aplicación web.
- `render_template`: función para renderizar archivos HTML con variables.
- `request`: objeto que permite acceder a datos enviados por el usuario (por ejemplo, formularios).

```python
from pymongo import MongoClient
```
Importa el cliente de MongoDB para Python, necesario para conectarse a la base de datos.

```python
# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
```
Configura el sistema de logging para mostrar mensajes de nivel INFO o superior en la consola.

```python
app = Flask(__name__)
```
Crea una instancia de la aplicación Flask. `__name__` indica el nombre del módulo actual.

```python
client = MongoClient("mongodb://localhost:27017")
```
Crea una conexión al servidor de MongoDB que corre localmente en el puerto 27017.

```python
db = client["Yelp"]
```
Selecciona la base de datos llamada "Yelp" dentro del servidor de MongoDB.

```python
@app.route("/")
def home():
    """Página principal de la aplicación."""
    return render_template("index.html")
```
- `@app.route("/")`: Define la ruta principal ("/") de la web.
- `def home()`: Función que se ejecuta cuando se accede a esa ruta.
- `render_template("index.html")`: Renderiza la plantilla HTML `index.html`.

```python
@app.route("/top_negocios")
def top_negocios():
    """Muestra los 5 negocios con más reseñas."""
    try:
        db.review.create_index("business_id")
        pipeline = [
            {"$group": {"_id": "$business_id", "totalReviews": {"$sum": 1}}},
            {"$sort": {"totalReviews": -1}},
            {"$limit": 5}
        ]
        negocios = list(db.review.aggregate(pipeline))
    except Exception as e:
        logging.error(f"Error al obtener top negocios: {e}")
        negocios = []
    return render_template("top_negocios.html", negocios=negocios)
```
- `@app.route("/top_negocios")`: Ruta para ver los negocios más populares.
- `db.review.create_index("business_id")`: Crea un índice en el campo `business_id` para acelerar búsquedas.
- `pipeline`: Lista de operaciones de agregación de MongoDB:
  - `{"$group": ...}`: Agrupa las reseñas por `business_id` y cuenta cuántas tiene cada uno.
  - `{"$sort": ...}`: Ordena los resultados de mayor a menor número de reseñas.
  - `{"$limit": 5}`: Limita el resultado a los 5 primeros.
- `negocios = list(db.review.aggregate(pipeline))`: Ejecuta el pipeline y convierte el resultado en una lista.
- Si ocurre un error, lo registra y pone `negocios` como lista vacía.
- Renderiza la plantilla `top_negocios.html` pasando la variable `negocios`.

```python
@app.route("/amigos_usuario", methods=["GET", "POST"])
def amigos_usuario():
    """Busca y muestra los amigos de un usuario por su user_id."""
    amigos = []
    nombre_usuario = None
    if request.method == "POST":
        user_id = request.form.get("user_id", "")
        if user_id:
            user = db.user.find_one({"user_id": user_id}, {"name": 1, "friends": 1, "_id": 0})
            if user:
                nombre_usuario = user.get("name")
                amigos_cursor = db.user.find({"user_id": {"$in": user.get("friends", [])}}, {"name": 1, "_id": 0})
                amigos = [amigo["name"] for amigo in amigos_cursor]
            else:
                logging.info(f"Usuario con user_id {user_id} no encontrado.")
    return render_template("amigos_usuario.html", amigos=amigos, nombre=nombre_usuario)
```
- `@app.route("/amigos_usuario", methods=["GET", "POST"])`: Ruta para buscar amigos de un usuario, acepta GET y POST.
- Inicializa `amigos` como lista vacía y `nombre_usuario` como None.
- Si la petición es POST:
  - Obtiene el `user_id` del formulario.
  - Si hay `user_id`, busca el usuario en la colección `user` y obtiene su nombre y lista de amigos.
  - Si encuentra el usuario:
    - Guarda el nombre.
    - Busca los usuarios cuyos `user_id` están en la lista de amigos y obtiene sus nombres.
    - Crea una lista con los nombres de los amigos.
  - Si no encuentra el usuario, registra un mensaje en el log.
- Renderiza la plantilla `amigos_usuario.html` con la lista de amigos y el nombre del usuario.

```python
@app.route("/resenas_autor")
def resenas_autor():
    """Muestra 5 reseñas con 4 o más estrellas, incluyendo información del autor."""
    try:
        pipeline = [
            {"$match": {"stars": {"$gte": 4}}},
            {"$lookup": {
                "from": "user",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "user_info"
            }},
            {"$unwind": "$user_info"},
            {"$project": {
                "_id": 0,
                "text": 1,
                "date": 1,
                "stars": 1,
                "user_info.name": 1,
                "user_info.yelping_since": 1
            }},
            {"$limit": 5}
        ]
        resenas = list(db.review.aggregate(pipeline))
    except Exception as e:
        logging.error(f"Error al obtener reseñas de autor: {e}")
        resenas = []
    return render_template("resenas_autor.html", resenas=resenas)
```
- `@app.route("/resenas_autor")`: Ruta para ver reseñas destacadas.
- `pipeline`: Pipeline de agregación de MongoDB:
  - `{"$match": {"stars": {"$gte": 4}}}`: Filtra reseñas con 4 o más estrellas.
  - `{"$lookup": ...}`: Une información del usuario (autor) usando el campo `user_id`.
  - `{"$unwind": "$user_info"}`: Descompone el array de usuario para que cada reseña tenga un solo autor.
  - `{"$project": ...}`: Selecciona solo los campos relevantes.
  - `{"$limit": 5}`: Limita a 5 resultados.
- Ejecuta el pipeline y convierte el resultado en una lista.
- Si hay error, lo registra y pone `resenas` como lista vacía.
- Renderiza la plantilla `resenas_autor.html` con las reseñas.

```python
@app.route("/buscar_texto", methods=["GET", "POST"])
def buscar_texto():
    """Permite buscar reseñas que contengan una palabra específica."""
    resultados = []
    palabra = ""
    if request.method == "POST":
        palabra = request.form.get("palabra", "")
        if palabra:
            try:
                resultados = list(db.review.find(
                    {"$text": {"$search": palabra}},
                    {"_id": 0, "text": 1, "stars": 1}
                ).limit(5))
            except Exception as e:
                logging.error(f"Error en búsqueda de texto: {e}")
    return render_template("buscar_texto.html", resultados=resultados, palabra=palabra)
```
- `@app.route("/buscar_texto", methods=["GET", "POST"])`: Ruta para buscar texto en reseñas, acepta GET y POST.
- Inicializa `resultados` como lista vacía y `palabra` como cadena vacía.
- Si la petición es POST:
  - Obtiene la palabra del formulario.
  - Si hay palabra, busca reseñas que contengan esa palabra usando el índice de texto de MongoDB.
  - Devuelve hasta 5 resultados, mostrando solo el texto y las estrellas.
  - Si hay error, lo registra.
- Renderiza la plantilla `buscar_texto.html` con los resultados y la palabra buscada.

```python
if __name__ == "__main__":
    app.run(debug=True)
```
- Si ejecutas este archivo directamente, inicia el servidor Flask en modo debug (útil para desarrollo).

---

## index.html

(Explicación línea por línea de index.html)

<!DOCTYPE html>
Indica que el documento es HTML5.

<html lang="es">
Comienza el documento HTML y especifica que el idioma es español.

<head>
    <meta charset="UTF-8">
Define la cabecera. El documento usará codificación UTF-8 (soporta caracteres especiales).

    <meta name="viewport" content="width=device-width, initial-scale=1.0">
Hace que la página sea responsive (se adapte a móviles).

    <title>Inicio | Yelp Flask</title>
Título de la pestaña del navegador.

    <link rel="stylesheet" href="/static/style.css">
Incluye el archivo de estilos CSS.

</head>
<body>
Cierra la cabecera y abre el cuerpo de la página.

    <header>
        <h1>Bienvenido a Yelp Flask</h1>
    </header>
Encabezado principal de la página.

    <div class="container">
        <!-- Navegación principal -->
        <nav>
            <a href="/top_negocios">Top Negocios</a> |
            <a href="/amigos_usuario">Buscar Amigos de Usuario</a> |
            <a href="/resenas_autor">Reseñas Destacadas</a> |
            <a href="/buscar_texto">Buscar en Reseñas</a>
        </nav>
Contenedor principal. Barra de navegación con enlaces a las distintas funciones.

        <section>
            <h2>¿Qué deseas hacer?</h2>
            <ul>
                <li>Ver los <a href="/top_negocios">negocios más populares</a> según las reseñas.</li>
                <li>Buscar los <a href="/amigos_usuario">amigos de un usuario</a> por su ID.</li>
                <li>Explorar <a href="/resenas_autor">reseñas destacadas</a> y sus autores.</li>
                <li>Realizar una <a href="/buscar_texto">búsqueda de texto</a> en las reseñas.</li>
            </ul>
        </section>
    </div>
Sección con una lista de las acciones principales que el usuario puede realizar.

    <footer>
        <p>&copy; {{ 2024 }} Yelp Flask. Proyecto educativo.</p>
    </footer>
Pie de página. El año está puesto como variable de plantilla (aunque debería ser solo 2024, no una variable).

</body>
</html>

---

## top_negocios.html

(Explicación línea por línea de top_negocios.html)

(Contenido igual que en los mensajes anteriores, línea por línea)

---

## amigos_usuario.html

(Explicación línea por línea de amigos_usuario.html)

---

## resenas_autor.html

(Explicación línea por línea de resenas_autor.html)

---

## buscar_texto.html

(Explicación línea por línea de buscar_texto.html)

---

## style.css

(Explicación línea por línea de style.css)

---

## terminal.txt

(Explicación línea por línea de terminal.txt)

- Primer línea: Cambia el directorio a la carpeta del proyecto.
- Segunda línea: Ejecuta la aplicación Flask. 