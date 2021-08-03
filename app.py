import hmac
import sqlite3
import datetime

from flask_cors import CORS

from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity


class User(object):

    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def init_user_table():
    conn = sqlite3.connect('online.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user"
                 "(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


def fetch_users():
    with sqlite3.connect('online.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


def init_products_table():
    with sqlite3.connect('online.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS post (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "name TEXT NOT NULL,"
                     "products TEXT NOT NULL,"
                     "price_of_product TEXT NOT NULL, "
                     "product_description TEXT NOT NULL)")
    print("products table created successfully.")


init_user_table()
init_products_table()

users = fetch_users()


username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'


jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect("online.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "username,"
                           "password) VALUES(?, ?, ?, ?)", (first_name, last_name, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201
        return response


@app.route('/create-products/', methods=["POST"])
@jwt_required()
def create_products():
    response = {}

    if request.method == "POST":
        name = request.form['name']
        price = request.form['price']
        product_description = request.form['product_description']
        date_created = datetime.datetime.now()

        with sqlite3.connect('online.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO post("
                           "name,"
                           "price,"
                           "product_description"
                           "date_created) VALUES(?, ?, ?)", (name, price, product_description, date_created))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "products added successfully"
        return response


@app.route('/get-products', methods=["GET"])
def get_products():
    response = {}
    with sqlite3.connect("online.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")

        products= cursor.fetchall()

    response['status_code'] = 200
    response['data'] = products
    return response


@app.route("/delete-products/<int:post_id>")
@jwt_required()
def delete_products(products_id):
    response = {}
    with sqlite3.connect("online.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=" + str(products_id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "product deleted successfully."
    return response


@app.route('/edit-products/<int:products_id>/', methods=["PUT"])
@jwt_required()
def edit_post(products_id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('online.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("name") is not None:
                put_data["name"] = incoming_data.get("name")
                with sqlite3.connect('online.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET name =? WHERE id=?", (put_data["name"], products_id))
                    conn.commit()
                    response['message'] = "Update was successful"
                    response['status_code'] = 200
            if incoming_data.get("name") is not None:
                put_data['name'] = incoming_data.get('name')

                with sqlite3.connect('online.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE post SET name =? WHERE id=?", (put_data["name"], products_id))
                    conn.commit()

                    response["name"] = " Name updated successfully"
                    response["status_code"] = 200
    return response


@app.route('/get-products/<int:products_id>/', methods=["GET"])
def get_products(products_id):
    response = {}

    with sqlite3.connect("online.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id=" + str(products_id))

        response["status_code"] = 200
        response["description"] = "products  retrieved successfully"
        response["data"] = cursor.fetchone()

    return jsonify(response)
