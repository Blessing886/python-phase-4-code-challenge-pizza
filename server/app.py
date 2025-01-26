#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class RestaurantsResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        restaurants_data = [restaurant.to_dict() for restaurant in restaurants]
        return make_response(jsonify(restaurants_data), 200)


api.add_resource(RestaurantsResource, "/restaurants")

class RestaurantByIdResource(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        
        restaurant_data = {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "restaurant_pizzas": [
                {
                    "id": rp.id,
                    "pizza": {
                        "id": rp.pizza.id,
                        "name": rp.pizza.name,
                        "ingredients": rp.pizza.ingredients,
                    },
                    "pizza_id": rp.pizza_id,
                    "price": rp.price,
                    "restaurant_id": rp.restaurant_id,
                }
                for rp in restaurant.restaurant_pizzas
            ],
        }
        return make_response(jsonify(restaurant_data), 200)

    
    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        RestaurantPizza.query.filter_by(restaurant_id=id).delete()

        db.session.delete(restaurant)
        db.session.commit()

        return make_response("", 204)
    
api.add_resource(RestaurantByIdResource, "/restaurants/<int:id>")

class PizzasResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        pizzas_data = [
            {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients,
            }
            for pizza in pizzas
        ]
        return make_response(jsonify(pizzas_data), 200)
    
api.add_resource(PizzasResource, "/pizzas")

class RestaurantPizzasResource(Resource):
    def post(self):
        data = request.get_json()
        if not all(key in data for key in ["price", "pizza_id", "restaurant_id"]):
            return make_response(jsonify({"errors": ["Missing required fields"]}), 400)
        price = data.get("price")
        if not (1 <= price <= 30):
            return make_response(jsonify({"errors": ["validation errors"]}), 400)
        
        pizza = Pizza.query.get(data.get("pizza_id"))
        restaurant = Restaurant.query.get(data.get("restaurant_id"))
        if not pizza or not restaurant:
            return make_response(jsonify({"errors": ["Pizza or Restaurant not found"]}), 404)
        
        # Create new RestaurantPizza
        try:
            restaurant_pizza = RestaurantPizza(
                price=data.get("price"),
                pizza_id=data.get("pizza_id"),
                restaurant_id=data.get("restaurant_id"),
            )
            db.session.add(restaurant_pizza)
            db.session.commit()

            response_data = {
                "id": restaurant_pizza.id,
                "pizza": {
                    "id": pizza.id,
                    "name": pizza.name,
                    "ingredients": pizza.ingredients,
                },
                "pizza_id": restaurant_pizza.pizza_id,
                "price": restaurant_pizza.price,
                "restaurant": {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "address": restaurant.address,
                },
                "restaurant_id": restaurant_pizza.restaurant_id,
            }
            return make_response(jsonify(response_data), 201)
        
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"errors": ["Validation errors"]}), 400)
        
api.add_resource(RestaurantPizzasResource, "/restaurant_pizzas")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
