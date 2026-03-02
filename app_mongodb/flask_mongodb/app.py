import logging
from flask import Flask, render_template, request
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017")
db = client["Yelp"]

@app.route("/")
def home():
    
    return render_template("index.html")

@app.route("/top_negocios")
def top_negocios():
    
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

@app.route("/amigos_usuario", methods=["GET", "POST"])
def amigos_usuario():
   
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

@app.route("/resenas_autor")
def resenas_autor():
    
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

@app.route("/buscar_texto", methods=["GET", "POST"])
def buscar_texto():
    
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

if __name__ == "__main__":
    app.run(debug=True)
