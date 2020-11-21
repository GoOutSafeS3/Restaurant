from datetime import date
import unittest 
import datetime

from restaurants.utils import *

from restaurants.worker import * 

from flask import current_app

class RestaurantsWorkerTests(unittest.TestCase):
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
