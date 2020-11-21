from datetime import date
import unittest 
import datetime
import dateutil

from requests.models import Response

from restaurants.app import create_app 
from restaurants.utils import restaurants, search_mock_restaurants, same_restaurants


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

    def test_get_restaurants(self):
        client = self.app.test_client()

        response = client.get('/restaurants')
        json = response.get_json()
        self.assertEqual(response.status_code, 200, msg=json)
        ret = same_restaurants(json, restaurants)
        self.assertIsNone(ret)

    def test_search_restaurants(self):
        client = self.app.test_client()
        queries = {
            "name": ["Rest","Rest 1", "", None],
            "opening_time": ["0","11","22","16","",None],
            "open_day": ["1","7","2","",None],
            "cuisine_type":["cuisine","adsad",None],
            "menu":["me","asdasd","",None],
        }
        keys = list(queries.keys())
        values = list(queries.values())
        import itertools
        for vals in itertools.product(*values):
            query = "?"
            for i in range(len(vals)):
                if vals[i] is not None:
                    query+=keys[i]+"="+vals[i]+"&"
            
            if query[-1] == "&":
                query = query[:-1]
            response = client.get('/restaurants'+query)
            json = response.get_json()
            if "" == vals[keys.index("opening_time")] or "" == vals[keys.index("open_day")]:
                self.assertEqual(response.status_code, 400, msg=json)
            else:
                self.assertEqual(response.status_code, 200, msg=json)
                rests = search_mock_restaurants(restaurants,keys,vals)
                ret = same_restaurants(json, rests)
                self.assertIsNone(ret, msg=query)
            
    def test_post_restaurants(self):
        client = self.app.test_client()

    def test_get_restaurant(self):
        client = self.app.test_client()

    def test_put_restaurant(self):
        client = self.app.test_client()

    def test_delete_restaurant(self):
        client = self.app.test_client()

    def test_get_restaurant_rate(self):
        client = self.app.test_client()

    def test_post_restaurant_rate(self):
        client = self.app.test_client()

    def test_get_tables(self):
        client = self.app.test_client()

    def test_get_table(self):
        client = self.app.test_client()

    def test_put_table(self):
        client = self.app.test_client()

    def test_delete_table(self):
        client = self.app.test_client()

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