######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
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
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_product(self):
        """Test Case to Read a Product"""
        test_product = self._create_products(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], test_product.name)

    def test_get_product_not_found(self):
        """Test case to read a product that doesn't exist"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("Not Found", data["message"])

    def test_update_product(self):
        """Test case to Update a product"""
        # create a product to update
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the product
        new_product = response.get_json()
        new_product["description"] = "unknown"
        response = self.client.put(f"{BASE_URL}/{new_product['id']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["description"],"unknown")

    def test_delete_product(self):
        """test case to Delete a product"""
         # create a list products containing 5 products using the _create_products() method. 
        products = self._create_products(5)
        # retrieve the number of products before deletion
        count = self.get_product_count()
        test_product= products[0]
        # send request to delete the test product
        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # check if the response data is empty 
        self.assertEqual(response.data,'')
        # send a get request to confirm the product does not exist
        response.self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # retrieve the count of products after the deletion operation
        after_count = self.get_product_count()
        # check if the new count of products is one less than the initial count
        self.assertEqual(after_count,count-1)

    def test_get_product_list(self):
        """Test case to List All products"""
        self._create_products(5)
        # send a self.client.get() request to the BASE_URL
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # get the data from the response in JSON format
        data = response.get_json()
        # assert that the len() of the data is 5 (the number of products you created)
        self.assertEqual(len(data),5)

    def test_query_by_name(self):
        """Test case to List By Name all products matching the name"""
        products = self._create_products(5)
        # get the name of the first product created
        test_name = products[0].name
        # count the number of products in the products list that have the same name as the test_name
        name_count = sum(p.name == test_name for p in products)
        # send an HTTP GET request to the URL specified by the BASE_URL variable, along with a query parameter "name"
        response = self.client.get(f"{BASE_URL}?name={test_name}")
        # assert that response status code is 200, indicating a successful request (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # retrieve the JSON data from the response
        data = response.get_json()
        # assert that the length of the data list (i.e., the number of products returned in the response) is equal to name_count
        self.assertEqual(len(data),name_count)
        # use a for loop to iterate through the products in the data list and checks if each product's name matches the test_name
        for prod in data:
            self.assertEqual(prod.name,test_name)
        
    def test_query_by_category(self):
        """Test case to List By Category products matching the category"""
        products = self._create_products(10)
        # retrieves the category of the first product in the products list and assigns it to the variable category
        category = products[0].category
        # create a list named found, containing products from the products list whose category matches the category variable
        found = [prod for prod in products if prod.category == category]
        # check the count of products match the specified category and assign it to the variable found_count
        found_count = len(found)
        # Log a debug message indicating the count and details of the products found
        logger.info("%s products found:%s",found_count, found.serialize())
        # send an HTTP GET request to the URL specified by the BASE_URL variable, along with a query parameter "category"
        response = self.client.get(f"{BASE_URL}?category={category}")
        # assert that response status code is 200, indicating a successful request (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # retrieve the JSON data from the response
        data = response.get_json()
        # assert that the length of the data list (i.e., the number of products returned in the response) is equal to found_count
        self.assertEqual(len(data),found_count)
        # use a for loop to check each product in the data list and verify that all returned products belong to the queried category
        for prod in data:
            self.asertEqual(prod.category,category)

    def test_qeury_by_availability(self):
        """Test case to List By Availability products matching the availability"""
        products = self._create_products(10)
        # list named available_products is initialized to store the products based on their availability status
        available_products = [prod for prod in products if prod.availabiity]
        # store the  count of available products.
        available_count = len(available_products)
        # Log a debug message indicating the count and details of the available products
        logger.info("%s products found: %s",available_count,available_products.serialize())
        # send an HTTP GET request to the URL specified by the BASE_URL variable, along with a query parameter "available" set to true.
        response = self.client.get(f"{BASE_URL}?availability=True")
        # assert that response status code is 200, indicating a successful request (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # retrieve the JSON data from the response
        data = response.get_json()
        # assert that the length of the data list (i.e., the number of products returned in the response) is equal to available_count
        self.assertEqual(len(data),available_count)
        # use a for loop to check each product in the data list and verify that the "available" attribute of each product is set to True
        for prod in data:
            self.asertEqual(prod.availabililty,True)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
