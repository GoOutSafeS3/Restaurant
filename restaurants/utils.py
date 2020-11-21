import datetime
import logging
import random
import os
import requests

from flask import current_app

from restaurants.orm import Restaurant, db, Rating, Table

from restaurants.errors import Error, Error400, Error404, Error500

""" The list of restaurants used when the mocks are required 
    
    They are identified starting from 1.
"""
restaurants = [
    {
        "url": "/restaurants/1", # NO OPENING TIMES
        "id": 1,
        "name": "Rest 1",
        "rating_val": 3.4,
        "rating_num": 123,
        "lat": 42.42,
        "lon": 42.42,
        "phone": "050123456",
        "first_opening_hour": 0,
        "first_closing_hour": 0,
        "second_opening_hour": None,
        "second_closing_hour": None,
        "occupation_time": 0,
        "cuisine_type": "cuisine_type",
        "menu": "menu",
        "closed_days": [1,2,3,4,5,6,7]
    },
    {
        "url": "/restaurants/2", # ONLY AT LUNCH (CLOSED ON MONDAYS)
        "id": 2,
        "name": "Rest 2",
        "rating_val": 3.4,
        "rating_num": 123,
        "lat": 42.42,
        "lon": 42.42,
        "phone": "050123456",
        "first_opening_hour": 10,
        "first_closing_hour": 14,
        "second_opening_hour": None,
        "second_closing_hour": None,
        "occupation_time": 1,
        "cuisine_type": "cuisine_type",
        "menu": "menu",
        "closed_days": [1]
    },
    {
        "url": "/restaurants/3", # ALWAYS OPEN (NEVER CLOSED)
        "id": 3,
        "name": "Rest 3",
        "rating_val": 3.4,
        "rating_num": 123,
        "lat": 42.42,
        "lon": 42.42,
        "phone": "050123456",
        "first_opening_hour": 0,
        "first_closing_hour": 23,
        "second_opening_hour": None,
        "second_closing_hour": None,
        "occupation_time": 2,
        "cuisine_type": "cuisine_type",
        "menu": "menu",
        "closed_days": []
    },
    {
        "url": "/restaurants/4", # TWO OPENINGS (CLOSED ON SUNDAY AND MONDAYS)
        "id": 4,
        "name": "Rest 4",
        "rating_val": 3.4,
        "rating_num": 123,
        "lat": 42.42,
        "lon": 42.42,
        "phone": "050123456",
        "first_opening_hour": 10,
        "first_closing_hour": 12,
        "second_opening_hour": 20,
        "second_closing_hour": 23,
        "occupation_time": 2,
        "cuisine_type": "cuisine_type",
        "menu": "menu",
        "closed_days": [1, 7]
    }
]

""" The list of tables for each restaurant used when the mocks are required 
    
    They are identified starting from 1.
"""
tables = [
    [{"id":1, "capacity":4}],
    [{"id":2, "capacity":3}],
    [{"id":4, "capacity":5}, {"id":5, "capacity":4}, {"id":6, "capacity":2}],
    [{"id":3, "capacity":2}]
]

def get_from(url):
    """ Makes a get request with a timeout.

    Returns the json object if the code is 200, otherwise None

    The timeout is set in config.ini or the default one is used (0.001)
    """
    try:
        with current_app.app_context():
            r = requests.get(url, timeout=current_app.config["TIMEOUT"])
            if r.status_code == 200:
                return r.json()
            return None
    except:
        return None

def get_restaurant(id):
    """ Get the restaurant json or None 
    
    Use the default ones if mocks are requested
    """
    with current_app.app_context():
        if current_app.config["USE_MOCKS"]:
            id -= 1 # restaurant IDs starting by 1
            if 0 <= id < len(restaurants):
                return restaurants[id]
            else:
                return None
        else:
            return get_from(current_app.config["REST_SERVICE_URL"]+"/restaurants/"+str(id))

def get_tables(id):
    """ Get the list fo the restaurant's tables or None 
    
    Use the default ones if mocks are requested
    """
    with current_app.app_context():
        if current_app.config["USE_MOCKS"]:
            id -= 1 # restaurant IDs starting by 1
            if 0 <= id < len(restaurants):
                return tables[id]
            else:
                return None
        else:
            return get_from(current_app.config["REST_SERVICE_URL"]+"/restaurants/"+str(id)+"/tables")

def same_restaurants(rests,rests2):
    if len(rests) != len(rests2):
        return "Different lenght"
    for rest,rest2 in zip(rests, rests2):
        for k in rest.keys():
            if k == "closed_days":
                if rest[k] != ''.join([str(i) for i in rest2[k]]):
                    return str(rest[k])+"\n"+k+"\n"+str(rest2[k])
            else:
                if rest[k] != rest2[k]:
                    return str(rest[k])+"\n"+k+"\n"+str(rest2[k])
    return None

def search_mock_restaurants(restaurants,keys,vals):
    res = []
    for r in restaurants:
        candidate = True
        for k,v in zip(keys,vals):
            if v is not None:
                if k == "opening_time":
                    v1 = False
                    v2 = False
                    if r["first_opening_hour"] is not None and r["first_closing_hour"] is not None:
                        v1 = r["first_opening_hour"] <= int(v) <= r["first_closing_hour"]
                    if r["second_opening_hour"] is not None and r["second_closing_hour"] is not None:
                        v2 = r["second_opening_hour"] <= int(v) <= r["second_closing_hour"]
                    if not(v1 or v2):
                        candidate = False
                elif k == "open_day":
                    if v in ''.join([str(i) for i in r["closed_days"]]):
                        candidate = False
                elif v not in r[k]:
                    candidate = False
        if candidate:
            res.append(r)
    return res

def validate_hours(first_opening, first_closing, second_opening, second_closing):
    """
    :type first_opening: Integer
    :type second_opening: Integer
    :type second_closing: Integer
    :type first_closing: Integer
    """
    if first_opening > first_closing or first_opening > second_opening or first_opening > second_closing:
        return False
    if first_closing > second_opening or first_closing > second_closing:
        return False
    if second_opening > second_closing:
        return False
    if second_closing > 24 and second_closing-24 > first_opening: # restaurant may be open after midnight, check that the opening the day after does not conflict with the closing
        return False
    return True

def valid_openings(first_opening_hour, first_closing_hour, second_opening_hour, second_closing_hour):
    if second_opening_hour is not None and first_opening_hour is not None and \
        first_closing_hour is not None and second_closing_hour is not None:
        if not validate_hours(first_opening_hour, first_closing_hour, second_opening_hour, second_closing_hour):
            return Error400("Closing time cannot be before opening time (general)").get()
    else:
        if first_opening_hour is None or first_closing_hour is None:
            if first_opening_hour is not None or first_closing_hour is not None:
                return Error400("You must specify both first opening hours or none").get()
            if second_opening_hour > second_closing_hour:
                return Error400("Closing time cannot be before opening time (second)").get()
        elif second_opening_hour is None or second_closing_hour is None:
            if second_opening_hour is not None or second_closing_hour is not None:
                return Error400("You must specify both second opening hours or none").get()
            if first_opening_hour > first_closing_hour:
                return Error400("Closing time cannot be before opening time (first)").get()
    return None

def edit_restaurant(restaurant_id, obj):
    try:
        restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).first()
        restaurant.id = obj["rest_id"]
        restaurant.name = obj["name"]
        restaurant.lat = obj["lat"]
        restaurant.lon = obj["lon"]
        restaurant.phone = obj["phone"]
        restaurant.first_opening_hour = obj["first_opening_hour"]
        restaurant.first_closing_hour = obj["first_closing_hour"]
        restaurant.second_opening_hour = obj["second_opening_hour"]
        restaurant.second_closing_hour = obj["second_closing_hour"]
        restaurant.occupation_time = obj["occupation_time"]
        restaurant.cuisine_type = obj["cuisine_type"]
        restaurant.menu = obj["menu"]
        restaurant.closed_days = ''.join([str(i) for i in obj["closed_days"]])
        db.session.add(restaurant)
        db.session.commit()
        return restaurant.id
    except:
        db.session.rollback()
        return None

def add_restaurant(obj):
    try:
        restaurant = Restaurant()
        restaurant.name = obj["name"]
        restaurant.lat = obj["lat"]
        restaurant.lon = obj["lon"]
        restaurant.phone = obj["phone"]
        restaurant.first_opening_hour = obj["first_opening_hour"]
        restaurant.first_closing_hour = obj["first_closing_hour"]
        restaurant.second_opening_hour = obj["second_opening_hour"]
        restaurant.second_closing_hour = obj["second_closing_hour"]
        restaurant.occupation_time = obj["occupation_time"]
        restaurant.cuisine_type = obj["cuisine_type"]
        restaurant.menu = obj["menu"]
        restaurant.closed_days = ''.join([str(i) for i in obj["closed_days"]])
        if "rating_val" in obj:
            restaurant.rating_val = obj["rating_val"]
        if "rating_num" in obj:
            restaurant.rating_num = obj["rating_num"]
        db.session.add(restaurant)
        db.session.commit()
        return restaurant.id
    except:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return None


def put_fake_data():
    """
    Enter fake data (useful for testing purposes).

    The properties of the "fake world" are described below
    """

    """
        BOOKINGS:
            - 1: FUTURE BOOKING 
                - USER 3 
                - REST 4 
                - TABLE 3
            - 2: FUTURE BOOKING 
                - USER 4
                - REST 3
                - TABLE 4
            - 3: OLD BOOKING 
                - USER 2
                - REST 2
                - TABLE 2
            - 4: OLD BOOKING 
                - USER 2
                - REST 2
                - TABLE 2
            - 5: FUTURE BOOKING 
                - USER 4
                - REST 3
                - TABLE 5
            - 6: OLD BOOKING 
                - USER 3
                - REST 3
                - TABLE 4
        USERS:
            - 1: NO BOOKINGS 
            - 2: 2 OLD BOOKINGS 
            - 3: 1 NEW AND 1 OLD 
            - 4: 2 NEW 
        
        RESTAURANTS:
            - 1: NO BOOKINGS 
            - 2: 2 OLD BOOKINGS 
            - 3: 2 NEW AND 1 OLD 
            - 4: 1 NEW 

        TABLES:
            - 1: NO BOOKINGS 
                - CAPACITY: 4
                - REST: 1
                - BOOKINGS: []
            - 2: 2 OLD BOOKINGS 
                - CAPACITY: 3
                - REST: 2
                - BOOKINGS: [3, 4]
            - 3: TABLE WITH A NEW BOOKING 
                - CAPACITY: 2
                - REST: 4
                - BOOKINGS: [1]
            - 4: TABLE WITH A OLD AND A NEW BOOKING
                - CAPACITY: 5
                - REST: 3
                - BOOKINGS: [2, 6]
            - 5: TABLE WITH A NEW BOOKING
                - CAPACITY: 4
                - REST: 3
                - BOOKINGS: [5]
            - 6: NO BOOKINGS
                - CAPACITY: 2
                - REST: 3
                - BOOKINGS: []
    """

    
    for restaurant in restaurants:
        add_restaurant(restaurant)

    obj = {
        "name": "",
        "lat": "",
        "lon": "",
        "phone": "",
        "first_opening_hour": "",
        "first_closing_hour": "",
        "second_opening_hour": "",
        "second_closing_hour": "",
        "occupation_time": "",
        "cuisine_type": "",
        "menu": "",
        "closed_days": ""
    }

    # add_booking(user_id, rest_id, number_of_people, booking_datetime, table_id)
    
    # 1: FUTURE BOOKING (USER 3, REST 4, TABLE 3)
    # add_booking(3, 4, 2, (datetime.datetime.now() + datetime.timedelta(days=2)), 3) 
    
    # # 2: FUTURE BOOKING (USER 4, REST 3, TABLE 4)
    # add_booking(4, 3, 1, (datetime.datetime.now() + datetime.timedelta(days=1)), 4)
    
    # # 3: OLD BOOKING (USER 2, REST 2, TABLE 2)
    # add_booking(2, 2, 3, (datetime.datetime.now()), 2)
    
    # # 4: OLD BOOKING (USER 2, REST 2, TABLE 2)
    # add_booking(2, 2, 3, (datetime.datetime.now() - datetime.timedelta(days=1)), 2)
    
    # # 5: FUTURE BOOKING (USER 4, REST 3, TABLE 5)
    # add_booking(4, 3, 1, (datetime.datetime.now() + datetime.timedelta(days=2)), 5)
    
    # # 6: OLD BOOKING (USER 3, REST 3, TABLE 4)
    # add_booking(3, 3, 1, (datetime.datetime.now() - datetime.timedelta(days=2)), 4)