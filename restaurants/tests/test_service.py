from datetime import date
import unittest 
import datetime
import dateutil

from requests.models import Response

from restaurants.app import create_app 


class BookingsTests(unittest.TestCase): 
    """ Tests endpoints with mocks """

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

    def test_edit_booking_400_409(self):
        client = self.app.test_client()

        # booking = {}
        # response = client.put('/restaurants/1',json=booking)
        # json = response.get_json()
        # self.assertEqual(response.status_code, 400, msg=json)


    def test_404(self): 
        client = self.app.test_client() 
        endpoints = { 
             "/restaurants/%d":(1,["get","put","delete"]) ,
             "/restaurants/%d/tables/%d": (2,["get","put","delete"])
         } 
        for k,(n,v) in endpoints.items(): 
            if n == 1:
                ids = 9999
            elif n==2:
                ids = (999,999)
            query = k%ids
            for m in v: 
                response = None 
                if m == "get": 
                    response = client.get(query) 
                elif m == "put": 
                    response = client.put(query,json={}) 
                elif m == "delete": 
                    response = client.delete(query) 
                self.assertIn(response.status_code, [400,404], msg="ENDPOINT: "+k+"\nMETHOD: "+m+"\n"+response.get_data(as_text=True)) 