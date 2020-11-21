from restaurants.tests.test_service import clone_for_post, table_post_keys
import unittest 
import datetime

import sys
sys.path.append("..")

from restaurants.app import create_app 
from restaurants.utils import tables

class RestaurantsFailureTests(unittest.TestCase): 
    """ Tests endpoints without mocks """

    ############################ 
    #### setup and teardown #### 
    ############################ 

    # executed prior to each test 
    def setUp(self): 
        app = create_app("FAILURE_TEST") 
        self.app = app.app 
        self.app.config['TESTING'] = True 

    # executed after each test 
    def tearDown(self): 
        pass 

###############
#### tests #### 
############### 

    def test_delete_table(self):
        # insert here check of the other endpoints like bookings
        client = self.app.test_client() 

        t = tables[1]
        dup = clone_for_post(t,table_post_keys)
        response = client.put(t["url"],json=dup)
        self.assertEqual(response.status_code, 500, msg=response.get_data()) 
        

   