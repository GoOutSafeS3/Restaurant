from datetime import date
import unittest 
import datetime

from restaurants.utils import get_restaurant, get_tables

from restaurants.app import create_app 

from flask import current_app

class RestaurantsUtilsTests(unittest.TestCase):
    """ Tests utility functions with and without mocks """

############################ 
#### setup and teardown #### 
############################ 

    # executed prior to each test 
    def setUp(self): 
        app = create_app("TEST") 
        self.app = app.app 
        self.app.config['TESTING'] = True 

    # executed after each test 
    def tearDown(self): 
        pass 

###############
#### tests #### 
############### 
    def test_get_a_table(self):
        now = datetime.datetime.now()

        with self.app.app_context():
            pass