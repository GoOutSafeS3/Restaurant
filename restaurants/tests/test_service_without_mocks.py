import unittest 
import datetime

import sys
sys.path.append("..")

from restaurants.app import create_app 

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
        pass
        # insert here check of the other endpoints like bookings
        # client = self.app.test_client() 
        # restaurant = {
        #     "user_id":1,
        #     "restaurant_id":3,
        #     "number_of_people":3, 
        #     "booking_datetime": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
        #     }
        # response = client.post('/restaurants',json=restaurant) 
        # json = response.get_json() 
        # self.assertEqual(response.status_code, 500, msg=json) 

   