import configparser

from flask import Flask, jsonify, request

import logging.config

from sqlalchemy import exc

from db import db
from product import Product

logging.config.fileConfig('/config/logging.ini', disable_existing_loggers=False)

log = logging.getLogger(__name__)


def get_database_url():
    config = configparser.ConfigParser()
    config.read('/config/db.ini')
    database_configuration = config['mysql']
    host = database_configuration['host']
    username = database_configuration['username']
    db_password = open('/run/secrets/db_password')
    password = db_password.read()
    database = database_configuration['database']

    database_url = f'mysql://{username}:{password}@{host}/{database}'
    log.info(f'Connecting to db: {database_url}')

    return database_url


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
db.init_app(app)


# curl -v http://localhost:5000/products
@app.route('/products')
def get_products():
    log.debug('GET /products')

    try:
        products = [product.json for product in Product.find_all()]
        return jsonify(products)
    except exc.SQLAlchemyError:
        log.exception('An exception occurred while retrieving all products.')
        return 'An exception occurred while retrieving all products.', 500


# curl -v http://localhost:5000/products/1
@app.route('/products/<int:_id>')
def get_product(_id):
    product = Product.find_by_id(_id)
    if product:
        return jsonify(product.json)

    return jsonify(product.json[0])


# curl --header "Content-Type: application/json" --request POST --data '{"name": "product 3"}' -v http://localhost:5000/products
@app.route('/products', methods=['POST'])
def post_product():
    request_product = request.json

    product = Product(None, request_product['name'])

    product.save_to_db()

    return jsonify(product.json), 201


# curl --header "Content-Type: application/json" --request PUT --data '{"name": "updated product"}' -v http://localhost:5000/products/1
@app.route('/products/<int:_id>', methods=['PUT'])
def put_product(_id):
    existing_product = Product.find_by_id(_id)

    if existing_product:
        updated_product = request.json

        existing_product.name = updated_product['name']
        existing_product.save_to_db()

        return jsonify(existing_product.json), 200

    return f'Product with id {_id} does not exist.', 404


# curl --request DELETE -v http://localhost:5000/products/1
@app.route('/products/<int:_id>', methods=['DELETE'])
def delete_product(_id):
    existing_product = Product.find_by_id(_id)

    if existing_product:
        existing_product.delete_from_db()
        return jsonify({"message": f"Deleted product with id {_id}"}), 200

    return f'Product with id {_id} does not exist.', 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
