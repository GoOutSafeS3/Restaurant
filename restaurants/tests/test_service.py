from datetime import date
from restaurants.background import check_ratings
import unittest 
import datetime
import dateutil

from requests.models import Response

from restaurants.app import create_app 
from restaurants.utils import get_mock_tables, tables, restaurants, search_mock_restaurants, same_restaurants, same_restaurant


restaurant_post_keys= [
    "name",
    "lat",
    "lon",
    "phone",
    "first_opening_hour",
    "first_closing_hour",
    "second_opening_hour",
    "second_closing_hour",
    "occupation_time",
    "cuisine_type",
    "menu",
    "closed_days",
]

table_post_keys= [
    "capacity",
]

def clone_for_post(obj,keys):
    dup = {}
    for k,v in obj.items():
        if k in keys:
            dup[k] = v
    return dup

restaurants_toaddedit = [
    {
        "url": "/restaurants/5",
        "id": 5,
        "name": "Rest 5",
        "rating_val": 0,
        "rating_num": 0,
        "lat": 42.41,
        "lon": 42.41,
        "phone": "050123456",
        "first_opening_hour": 2,
        "first_closing_hour": 5,
        "second_opening_hour": None,
        "second_closing_hour": None,
        "occupation_time": 1,
        "cuisine_type": "cuisine_type",
        "menu": "menu",
        "closed_days": [1,2,3,4,5,6,7]
    },
    {
        "url": "/restaurants/2", # ONLY AT LUNCH (CLOSED ON MONDAYS)
        "id": 2,
        "name": "Rest 2-new",
        "rating_val": 3,
        "rating_num": 1,
        "lat": 42.41,
        "lon": 42.41,
        "phone": "050123456",
        "first_opening_hour": None,
        "first_closing_hour": None,
        "second_opening_hour": 20,
        "second_closing_hour": 23,
        "occupation_time": 1,
        "cuisine_type": "cuisine_type new",
        "menu": "menu-new",
        "closed_days": [1]
    },
    {
        "url": "/restaurants/6",
        "id": 6,
        "name": "Rest 6",
        "rating_val": 0,
        "rating_num": 0,
        "lat": 42.41,
        "lon": 42.41,
        "phone": "050123456",
        "first_opening_hour": 2,
        "first_closing_hour": 5,
        "second_opening_hour": None,
        "second_closing_hour": None,
        "occupation_time": 1,
        "cuisine_type": "cuisine_type",
        "menu": "menu",
        "closed_days": [1,2,3,4,5,6,7]
    }
]

opening_possibilities = [
    {
        "first_opening_hour": "12", 
        "first_closing_hour": "11", #wrong hours at lunch
        "second_opening_hour": "19",
        "second_closing_hour": "23",
    },
    {
        "first_opening_hour": "12", 
        "first_closing_hour": "15",
        "second_opening_hour": "19",
        "second_closing_hour": "18",
    },
    {
        "first_opening_hour": "12", 
        "first_closing_hour": "15",
        "second_opening_hour": "19",
        "second_closing_hour": "37",
    },
    {
        "first_opening_hour": "12", 
        "first_closing_hour": "20",
        "second_opening_hour": "19",
        "second_closing_hour": "22",
    },
    {
        "first_opening_hour": "20", 
        "first_closing_hour": "22",
        "second_opening_hour": "12",
        "second_closing_hour": "15",
    },
    {
        "first_opening_hour": None, 
        "first_closing_hour": None,
        "second_opening_hour": "23",
        "second_closing_hour": "19",
    },
    {
        "first_opening_hour": "15", 
        "first_closing_hour": "12",
        "second_opening_hour": None,
        "second_closing_hour": None,
    },
    {
        "first_opening_hour": "11", 
        "first_closing_hour": None,
        "second_opening_hour": "16",
        "second_closing_hour": None,
    },
    {
        "first_opening_hour": None, 
        "first_closing_hour": None,
        "second_opening_hour": "16",
        "second_closing_hour": None,
    }
]

table_possibilities = [
    {
        "capacity": -1
    },
    {
        "capacity": 0
    },
    {
        "capacity": -10
    },
]

ratings_toadd = [
    {"rater_id": 1, "rating": 3},
    {"rater_id": 2, "rating": 6}, # invalid
]

tables_toaddedit = [
    {"url": "/restaurants/5/tables/7", "id":7, "restaurant_id": 5, "capacity":2},
    {"url": "/restaurants/5/tables/7", "id":7, "restaurant_id": 5, "capacity":5},
    {"url": "/restaurants/1/tables/8", "id":8, "restaurant_id": 5, "capacity":5},
]

class RestaurantsTests(unittest.TestCase): 
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
        dup = clone_for_post(restaurants_toaddedit[0], restaurant_post_keys)
        response = client.post('/restaurants',json=dup)
        json = response.get_json()
        ret = same_restaurant(json, restaurants_toaddedit[0])
        self.assertIsNone(ret, msg=str(json)+"\n\n"+str(restaurants_toaddedit[0]))
        self.assertEqual(response.status_code, 201, msg=json)

    
    def test_post_restaurants_failures(self):
        client = self.app.test_client()
        
        dup_=clone_for_post(restaurants_toaddedit[0], restaurant_post_keys)

        for k,v in dup_.items():
            dup = dup_.copy()
            if v == None:
                continue
            dup[k] = None
            response = client.post("/restaurants",json=dup)
            json = response.get_json()
            self.assertEqual(response.status_code, 400, msg=json)

        for pos in opening_possibilities:
            dup = clone_for_post(restaurants_toaddedit[0], restaurant_post_keys)
            for k,v in pos.items():
                dup[k] = v
            response = client.post("/restaurants",json=dup)
            json = response.get_json()
            self.assertEqual(response.status_code, 400, msg=json)
            

    def test_get_restaurant(self):
        client = self.app.test_client()

        for r in restaurants:
            response = client.get(r['url'])
            json = response.get_json()
            self.assertEqual(response.status_code, 200, msg=json)
            ret = same_restaurant(json, r)
            self.assertIsNone(ret, msg=str(json)+"\n\n"+str(r))

    def test_put_restaurant(self):
        client = self.app.test_client()

        dup = clone_for_post(restaurants_toaddedit[1], restaurant_post_keys)
        response = client.put(restaurants_toaddedit[1]["url"], json=dup)
        json = response.get_json()
        self.assertEqual(response.status_code, 200, msg=json)
        ret = same_restaurant(json, restaurants_toaddedit[1])
        self.assertIsNone(ret, msg=str(json)+"\n\n"+str(restaurants_toaddedit[1]))

    def test_put_restaurants_failures(self):
        client = self.app.test_client()
        
        dup_=clone_for_post(restaurants_toaddedit[0], restaurant_post_keys)

        for k,v in dup_.items():
            dup = dup_.copy()
            dup[k] = None
            if v == None:
                continue
            response = client.put(restaurants[0]["url"],json=dup)
            json = response.get_json()
            self.assertEqual(response.status_code, 400, msg=json)

        for pos in opening_possibilities:
            dup = clone_for_post(restaurants_toaddedit[0], restaurant_post_keys)
            for k,v in pos.items():
                dup[k] = v
            response = client.put(restaurants[0]["url"],json=dup)
            json = response.get_json()
            self.assertEqual(response.status_code, 400, msg=json)

    def test_delete_restaurant(self):
        client = self.app.test_client()
        # assuming test_post_restaurants executed before
        self.test_post_restaurants()
        r = restaurants_toaddedit[0]

        response = client.delete(r["url"])
        json = response.get_data()
        self.assertEqual(response.status_code, 204, msg=json)

        response = client.get(r["url"])
        json = response.get_json()
        self.assertEqual(response.status_code, 404, msg=json)

        response = client.delete(restaurants[3]["url"])
        json = response.get_data()
        self.assertEqual(response.status_code, 409, msg=json)

        response = client.get(restaurants[3]["url"])
        json = response.get_json()
        self.assertEqual(response.status_code, 200, msg=json)

        #check incremental id
        r = restaurants_toaddedit[2]
        dup = clone_for_post(r, restaurant_post_keys)
        response = client.post('/restaurants',json=dup)
        json = response.get_json()
        ret = same_restaurant(json, r)
        self.assertIsNone(ret, msg=str(json)+"\n\n"+str(r))
        self.assertEqual(response.status_code, 201, msg=json)

    def test_get_restaurant_rate(self):
        client = self.app.test_client()
        for r in restaurants:
            response = client.get("/restaurants/%d/rate" % r["id"])
            json = response.get_json()
            self.assertEqual(response.status_code, 200, msg=json)
            self.assertEqual(json["rating"], r["rating_val"], msg =json)
            self.assertEqual(json["ratings"], r["rating_num"], msg =json)

    def test_post_restaurant_rate(self):
        client = self.app.test_client()
        r = restaurants[0]
        response = client.post("%s/rate" % r["url"], json=ratings_toadd[0])
        self.assertEqual(response.status_code, 202, msg=response.get_data())

        check_ratings.apply()

        response = client.get("%s/rate" % r["url"])
        json = response.get_json()
        self.assertEqual(response.status_code, 200, msg=json)
        self.assertEqual(json["rating"], ratings_toadd[0]["rating"], msg =json)
        self.assertEqual(json["ratings"], 1, msg =json)

    def test_post_restaurant_rate_failures(self):
        client = self.app.test_client()
        r = restaurants[1]

        response = client.post("%s/rate" % r["url"], json=ratings_toadd[1])
        self.assertEqual(response.status_code, 400, msg=response.get_data())

        response = client.get("%s/rate" % r["url"])
        json = response.get_json()
        self.assertEqual(response.status_code, 200, msg=json)
        self.assertEqual(json["rating"], r["rating_val"], msg =json)
        self.assertEqual(json["ratings"], r["rating_num"], msg =json)


    def test_get_tables(self):
        client = self.app.test_client()

        for r in restaurants:
            response = client.get(r["url"]+"/tables")
            ret = get_mock_tables(tables, r["id"])
            if len(ret) == 0:
                self.assertEqual(response.status_code, 204, msg=response.get_data())
            else:
                json = response.get_json()
                self.assertEqual(response.status_code, 200, msg=json)
                self.assertEqual(ret, json)

    def test_post_tables(self):
        client = self.app.test_client()
        # assuming test_post_restaurant executed before
        self.test_post_restaurants()

        r = restaurants_toaddedit[0]
        t = tables_toaddedit[0]
        dup = clone_for_post(t,table_post_keys)

        response = client.post(r["url"]+"/tables")
        json = response.get_json()
        self.assertEqual(response.status_code, 201, msg=json)
        self.assertEqual(t, json)

    def test_post_tables_failures(self):
        client = self.app.test_client()

        dup_=clone_for_post(tables_toaddedit[0], table_post_keys)

        for k,v in dup_.items():
            dup = dup_.copy()
            if v == None:
                continue
            dup[k] = None
            dup = clone_for_post(dup, table_post_keys)
            response = client.post("/restaurants/%d/tables" % tables_toaddedit[0]["restaurant_id"],json=dup)
            json = response.get_json()
            self.assertEqual(response.status_code, 400, msg=json)

        for pos in table_possibilities:
            dup_ = clone_for_post(tables_toaddedit[0], table_post_keys)
            for k,v in pos.items():
                dup_[k] = v
            dup = clone_for_post(dup_, table_post_keys)
            response = client.post("/restaurants/%d/tables" % dup_["restaurant_id"],json=dup)
            json = response.get_json()
            self.assertEqual(response.status_code, 400, msg=json)

    def test_get_table(self):
        client = self.app.test_client()

        for t in tables:
            response = client.get(t["url"])
            self.assertEqual(response.status_code, 200, msg=response.get_data())
            json = response.get_json()
            self.assertEqual(json,t)

    def test_put_table(self):
        # assuming test_post_table executed before
        self.test_post_tables()

        client = self.app.test_client()
        t = tables_toaddedit[1]
        dup = clone_for_post(t,table_post_keys)
        response = client.put(t["url"],json=dup)
        self.assertEqual(response.status_code, 200, msg=response.get_data())
        json = response.get_json()
        self.assertEqual(json,t)

    def test_put_table_failures(self):
        client = self.app.test_client()
        # assuming test_post_restaurant executed before
        self.test_post_restaurants()

        dup_=clone_for_post(tables[0], table_post_keys)

        for k,v in dup_.items():
            dup = dup_.copy()
            if v == None:
                continue
            dup[k] = None
            dup = clone_for_post(dup, table_post_keys)
            response = client.put(tables[0]["url"],json=dup)
            json = response.get_json()
            self.assertEqual(response.status_code, 400, msg=json)

        for pos in table_possibilities:
            dup_ = clone_for_post(tables[0], table_post_keys)
            for k,v in pos.items():
                dup_[k] = v
            dup = clone_for_post(dup_, table_post_keys)
            response = client.put(dup_["url"],json=dup)
            json = response.get_json()
            self.assertEqual(response.status_code, 400, msg=json)


    def test_delete_table(self):
        client = self.app.test_client()
        # assuming test_post_tables executed before
        self.test_post_tables()
        t = tables_toaddedit[0]

        response = client.delete(t["url"])
        json = response.get_data()
        self.assertEqual(response.status_code, 204, msg=json)

        response = client.get(t["url"])
        json = response.get_json()
        self.assertEqual(response.status_code, 404, msg=json)

        response = client.delete(tables[2]["url"])
        json = response.get_data()
        self.assertEqual(response.status_code, 409, msg=json)

        response = client.get(restaurants[2]["url"])
        json = response.get_json()
        self.assertEqual(response.status_code, 200, msg=json)

        # check incremental id
        t = tables_toaddedit[2]
        dup = clone_for_post(t, table_post_keys)
        response = client.post('/restaurants/%d/tables'%t["restaurant_id"],json=dup)
        json = response.get_json()
        ret = same_restaurant(json, t)
        self.assertIsNone(ret, msg=str(json)+"\n\n"+str(t))
        self.assertEqual(response.status_code, 201, msg=json)
        

    def test_404(self): 
        client = self.app.test_client() 
        endpoints = { 
             "/restaurants/%d":(1,["get","put","delete"],clone_for_post(restaurants[0],restaurant_post_keys)),
             "/restaurants/%d/tables/%d": (2,["get","put","delete"],clone_for_post(tables[0],table_post_keys)),
             "/restaurants/%d/tables": (1,["post"],clone_for_post(tables_toaddedit[0],table_post_keys))
         } 
        for k,(n,v,json) in endpoints.items(): 
            if n == 1:
                ids = 9999
            elif n==2:
                ids = (999,999)
            query = k%ids
            for m in v: 
                response = None 
                if m == "get": 
                    response = client.get(query) 
                elif m == "post":
                    response = client.post(query,json=json)
                elif m == "put": 
                    response = client.put(query,json=json) 
                elif m == "delete": 
                    response = client.delete(query) 
                self.assertIn(response.status_code, [400,404], msg="ENDPOINT: "+k+"\nMETHOD: "+m+"\n"+response.get_data(as_text=True)) 