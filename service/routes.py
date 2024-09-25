######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

# spell: ignore Rofrano jsonify restx dbname
"""
Product Store Service with UI
"""
from flask import jsonify, request, abort
from flask import url_for  # noqa: F401 pylint: disable=unused-import
from service.models import Product
from service.common import status  # HTTP Status Codes
from . import app


######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# C R E A T E   A   N E W   P R O D U C T
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    message = product.serialize()

    location_url = url_for("get_products", product_id=product.id, _external=True)
    
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# L I S T   A L L   P R O D U C T S
######################################################################
@app.route("/products", methods=["GET"])
def list_products():
    """Returns a list of Products"""
    app.logger.info("Request to list Products...")
    # use the Product.all() method to retrieve all products
    # create a list of serialize() products
    # log the number of products being returned in the list 
    # return the list with a return code of status.HTTP_200_OK
    # return {list of products as json here + 200}

######################################################################
# LIST PRODUCTS BY NAME
######################################################################
#@app.route("/products", methods=["GET"])
#def list_products():
  #  """Returns a list of Products"""
  #  app.logger.info("Request to list Products...")

    # Initialize an empty list to hold the products.
    # Get the `name` parameter from the request (hint: use `request.args.get()`
    # test to see if you received the "name" query parameter
    # If you did, call the Product.find_by_name(name) method to retrieve products that match the specified name
    # If you didn't call list all
   # products = Product.all()

  #  results = [product.serialize() for product in products]
  #  app.logger.info("[%s] Products returned", len(results))
  #  return results, status.HTTP_200_OK

######################################################################
# LIST PRODUCTS BY CATEGORY
######################################################################
#@app.route("/products", methods=["GET"])
#def list_products():
 #   """Returns a list of Products"""
 #   app.logger.info("Request to list Products...")

#    products = []
#    name = request.args.get("name")
    # Get the `category` parameter from the request (hint: use `request.args.get()`

 #   if name:
  #      app.logger.info("Find by name: %s", name)
  #      products = Product.find_by_name(name)

    # test to see if you received the "category" query parameter
    # If you did, convert the category string retrieved from the query parameters to the corresponding enum value from the Category enumeration
    # call the Product.find_by_category(category_value) method to retrieve products that match the specified category_value

   # else:
  #      app.logger.info("Find all")
   #     products = Product.all()

  #  results = [product.serialize() for product in products]
  #  app.logger.info("[%s] Products returned", len(results))
   # return results, status.HTTP_200_OK

######################################################################
# LIST PRODUCTS BY AVAILABILITY
######################################################################
#@app.route("/products", methods=["GET"])
#def list_products():
  #  """Returns a list of Products"""
  #  app.logger.info("Request to list Products...")

 #   products = []
 #   name = request.args.get("name")
 #   category = request.args.get("category")
    # Get the `available` parameter from the request (hint: use `request.args.get()`

   # if name:
 #       app.logger.info("Find by name: %s", name)
   #     products = Product.find_by_name(name)
 #   elif category:
   #     app.logger.info("Find by category: %s", category)
        # create enum from string
   #     category_value = getattr(Category, category.upper())
    #    products = Product.find_by_category(category_value)

    # test to see if you received the "available" query parameter
    # If you did, convert the available string retrieved from the query parameters to a boolean value
    # call the Product.find_by_availability(available_value) method to retrieve products that match the specified available_value
    # otherwise list all products

  #  else:
 #       app.logger.info("Find all")
  #      products = Product.all()

  #  results = [product.serialize() for product in products]
  #  app.logger.info("[%s] Products returned", len(results))
 #   return results, status.HTTP_200_OK

######################################################################
# R E A D   A   P R O D U C T
######################################################################
@app.route("/products/<int:product_id>", methods=["GET"])
def get_products(product_id):
    """Retrieve a single Product by ID"""
    app.logger.info("Request to retrieve a product with id [%s]", product_id)
    product = Product.find(product_id)
    if not product:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Could not find product with ID {product_id}"
        )

    app.logger.info("Returning product: %s", product.name)
    return product.serialize(), status.HTTP_200_OK

######################################################################
# U P D A T E   A   P R O D U C T
######################################################################
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_products(product_id):
    """Update a product with the product ID using the posted body"""
    app.logger.info("Request to update a product with id [%s]", product_id)
    check_content_type("application/json")

    product = Product.find(product_id)
    if not product:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Could not find product with ID '{product_id}'"
        )
    product.deserialize(request.get_json())
    product.id = product_id
    product.update()
    return product.serialize(), status.HTTP_200_OK

######################################################################
# D E L E T E   A   P R O D U C T
######################################################################
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_products(product_id):
    """
    Delete a Product
    This endpoint will delete a Product based the id specified in the path
    """
    app.logger.info("Request to Delete a product with id [%s]", product_id)
    # use the Product.find() method to retrieve the product by the product_id
    # if found, call the delete() method on the product
    # return and empty body ("") with a return code of status.HTTP_204_NO_CONTENT
    # return {empty string + 204}
