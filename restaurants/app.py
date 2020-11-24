from datetime import date
from logging import debug
from restaurants.background import init_celery
import connexion
import datetime
import logging
import configparser
import sys
import os
import dateutil.parser

from flask import current_app

from connexion import NoContent, request

from restaurants.orm import db, Restaurant,Rating,Table

from restaurants.utils import add_rating, add_table, del_restaurant, del_table, edit_table, get_future_bookings, put_fake_data, valid_openings, add_restaurant, edit_restaurant, valid_rating

from restaurants.errors import Error, Error400, Error404, Error409, Error500

import sys
sys.path.append("./restaurants/")

"""
The default app configuration: 
in case a configuration is not found or 
some data is missing
"""
DEFAULT_CONFIGURATION = { 

    "FAKE_DATA": False, # insert some default data in the database (for tests)
    "REMOVE_DB": False, # remove database file when the app starts
    "DB_DROPALL": False,

    "IP": "0.0.0.0", # the app ip
    "PORT": 8080, # the app port
    "DEBUG":True, # set debug mode

    "SQLALCHEMY_DATABASE_URI": "db/restaurants.db", # the database path/name
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,

    "USE_MOCKS": False, # use mocks for external calls
    "TIMEOUT": 2, # timeout for external calls
    "BOOK_SERVICE_URL": "http://bookings:8080", # bookings microservice url

    "COMMIT_RATINGS_AFTER": 10, # celery config for updating the ratings
    "result_backend" : os.getenv("BACKEND", "redis://localhost:6379"),
    "broker_url" : os.getenv("BROKER", "redis://localhost:6379"),
}

def get_restaurants(name=None, opening_time=None, open_day=None, cuisine_type=None, menu=None):
    """ Return the list of restaurants.

    GET /restaurants?[name=N_ID&][opening_time=TIME_ID&][open_day=DAY_ID&][cuisine_type=CUISINE_DT&][menu=MENU_DT&]

    It's possible to filter the restaurants thanks the query's parameters.
    The parameters can be overlapped in any way.
    All paramters are optional.

    - name: Restaruant that match the given name
    - opening_time: All restaurants that are open at that hour
    - open_day: All restaurants that are open in that day
    - cuisine_type: All restaurants that match the cuisine type
    - menu: All restaurants that match the menu

    Status Codes:
        200 - OK
        400 - Something wrong in the openings
    """

    q = db.session.query(Restaurant)
    if name is not None:
        q = q.filter(Restaurant.name.contains(name))
    if opening_time is not None:
        if opening_time >= 0 and opening_time <= 23:
            q = q.filter(
                    (Restaurant.first_opening_hour.isnot(None) & Restaurant.first_closing_hour.isnot(None) & 
                        (Restaurant.first_opening_hour <= opening_time)
                        &
                        (opening_time <= Restaurant.first_closing_hour)
                    )
                    |
                    (Restaurant.second_opening_hour.isnot(None) & Restaurant.second_closing_hour.isnot(None) & 
                        (Restaurant.second_opening_hour <= opening_time)
                        &
                        (opening_time <= Restaurant.second_closing_hour)
                    )
                )
        else:
            return Error400("Argument: opening_time is not a valid hour").get()
    if open_day is not None:
        if open_day >= 1 and open_day <= 7:
            q = q.filter(~Restaurant.closed_days.contains(str(open_day)))
        else:
            return Error400("Argument: open_day is not a valid day").get()
    if cuisine_type is not None:
        q = q.filter(Restaurant.cuisine_type.contains(cuisine_type))
    if menu is not None:
        q = q.filter(Restaurant.menu.contains(menu))

    return [p.dump() for p in q], 200

def post_restaurants():
    """ Add a new restaurant.

    POST /restaurants
    
    Returns the restaurant if it can be made, otherwise returns an error message.

    Requires a json object with:
        - name
        - lat
        - lon
        - phone
        - first_opening_hour
        - first_closing_hour
        - second_opening_hour
        - second_closing_hour
        - occupation_time
        - cuisine_type
        - menu
        - closed_days

    Status Codes:
        201 - The restaurant has been created
        400 - Data error
        500 - DB error
    """

    req = request.json
    err = valid_openings(req["first_opening_hour"],req["first_closing_hour"],req["second_opening_hour"],req["second_closing_hour"])
    if err is not None:
        return err

    rest_id = add_restaurant(req)

    restaurant, status_code = get_restaurant(rest_id)
    if status_code == 200:
        return restaurant, 201
    else: # unexpected error
        return Error500().get()

def get_restaurant(restaurant_id):
    """ Return a specific restaurant (request by id)

    GET /restaurants/{restaurant_id}

        Status Codes:
            200 - OK
            404 - Restaurant not found
    """
    q = db.session.query(Restaurant).filter_by(id = restaurant_id).first()
    if q is None:
        return Error404("Restaurant not found").get()
    return q.dump(), 200

def put_restaurant(restaurant_id):
    """ Return a specific restaurant (request by id)

    GET /restaurants/{restaurant_id}

        Status Codes:
            200 - OK
            404 - Restaurant not found
            409 - The restaurant has pending reservations tha conflict with the new times, those must be deleted first
            500 - DB error
    """
    p = db.session.query(Restaurant).filter_by(id = restaurant_id).first()
    if p is None:
        return Error404("Restaurant not found").get()
        
    req = request.json
    err = valid_openings(req["first_opening_hour"],req["first_closing_hour"],req["second_opening_hour"],req["second_closing_hour"])
    if err is not None:
        return err

    array,code = get_future_bookings(restaurant_id)
    if code == 200:
        for booking in array:
            hour = dateutil.parser.parse(booking["booking_datetime"]).hour()
            if not (req["first_opening_hour"] <= hour <= req["first_closing_hour"]
                    or 
                    req["second_opening_hour"] <= hour <= req["second_closing_hour"]):
                return Error409("The restaurant has pending reservations tha conflict with the new times, those must be deleted first").get()
    else:
        return Error500().get()

    rest_id = edit_restaurant(restaurant_id, req)

    restaurant, status_code = get_restaurant(rest_id)
    if status_code == 200:
        return restaurant, 200
    else: # unexpected error
        return Error500().get()

def delete_restaurant(restaurant_id):
    """ Delete a restaurant specified by the id.

    DELETE /restaurants/{restaurant_id}
    
    Deletion is only possible if the restaurant has not yet passed.

    Otherwise it remains stored (necessary for contact tracing)

    Status Codes:
        204 - Deleted
        404 - Restaurant not found
        409 - The restaurant has pending reservations, those must be deleted first
        500 - Error with the database or the other bookings service
    """
    p = db.session.query(Restaurant).filter_by(id = restaurant_id).first()
    if p is None:
        return Error404("Restaurant not found").get()

    array,code = get_future_bookings(restaurant_id)
    if code != 200:
        return Error500().get() # Cannot connect to the bookings service

    if len(array) != 0:
        return Error409("The restaurant has pending reservations, those must be deleted first").get()

    if not del_restaurant(restaurant_id):
        return Error500().get() # DB error

    return NoContent, 204

def get_restaurant_rating(restaurant_id):
    """ Return the rating of a specific restaurant (request by id)

    GET /restaurants/{restaurant_id}/rate

        Status Codes:
            200 - OK
            404 - Restaurant not found
    """
    q = db.session.query(Restaurant).filter_by(id = restaurant_id).first()
    if q is None:
        return Error404("Restaurant not found").get()
    return q.dump_rating(), 200

def post_restaurant_rating(restaurant_id):
    """ Add a new rating for the restaurant.

    POST /restaurants/{restaurant_id}/rate
    
    Returns the restaurant if it can be made, otherwise returns an error message.

    Requires a json object with:
        - rater_id
        - rating

    Status Codes:
        202 - The ratingg for the restaurant has been created
        400 - Bad request or Restaurant already rated by the user
        404 - Restaurant not found
        500 - DB error
    """
    req = request.json
    err = valid_rating(req, restaurant_id)
    if err is not None:
        return err

    code = add_rating(req, restaurant_id)
    if code is None:
        return Error500().get()

    if valid_rating(req, restaurant_id) is not None:
        return NoContent, 202
    else: # unexpected error
        return Error500().get()

def get_restaurant_tables(restaurant_id, capacity=None):
    """ Return the tables of a restaurant (request by id)

    GET /restaurants/{restaurant_id}/tables?capacity=CAPACITY
    
    capacity is optional and specify the minimum capacity the returned tables should have

        Status Codes:
            200 - OK
            204 - No tables with such capacity or no tables
            404 - Restaurant not found
    """
    q = db.session.query(Restaurant).filter(Restaurant.id == restaurant_id)
    if q is None:
        return Error404("Restaurant not found").get()

    q = db.session.query(Table).filter(Table.restaurant_id == restaurant_id)
    if capacity is not None:
        q = q.filter(Table.capacity >= capacity)

    q = q.all()

    if len(q)==0:
        return NoContent, 204
    return [q.dump() for q in q], 200

def post_restaurant_table(restaurant_id):
    """ Add a new table for the restaurant.

    POST /restaurants/{restaurant_id}/tables
    
    Returns the restaurant if it can be made, otherwise returns an error message.

    Requires a json object with:
        - capacity

    Status Codes:
        201 - The restaurant has been created
        400 - Data error
        404 - Restaurant not found
        500 - DB error
    """

    req = request.json

    r = db.session.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if r is None:
        return Error404("Restaurant not found").get()

    table_id = add_table(req, restaurant_id)

    table, status_code = get_restaurant_table(restaurant_id, table_id)
    if status_code == 200:
        return table, 201
    else: # unexpected error
        return Error500().get()

def get_restaurant_table(restaurant_id, table_id):
    """ Return a specific restaurant (request by id)

    GET /restaurants/{restaurant_id}/tables/{table_id}

        Status Codes:
            200 - OK
            400 - Data error
            404 - Restaurant or Table not found
            500 - DB error
    """
    q = db.session.query(Table).filter(Table.id == table_id and Table.restaurant_id == restaurant_id).first()
    if q is None:
        return Error404("Restaurant or Table not found").get()
    return q.dump(), 200

def put_restaurant_table(restaurant_id, table_id):
    """ Return a specific restaurant (request by id)

    GET /restaurants/{restaurant_id}/tables/{table_id}

        Status Codes:
            200 - OK
            404 - Restaurant not found
            409 - The table has pending reservations tha conflict with the new capacity, those must be deleted first
            500 - DB error
    """
    req = request.json

    q = db.session.query(Table).filter(Table.id == table_id and Table.restaurant_id == restaurant_id).first()
    if q is None:
        return Error404("Restaurant or Table not found").get()

    array,code = get_future_bookings(restaurant_id, table_id)
    if code == 200:
        for booking in array:
            if booking["number_of_people"] > req["capacity"]:
                return Error409("The table has pending reservations tha conflict with the new capacity, those must be deleted first").get()
    else:
        return Error500().get()

    table_id2 = edit_table(table_id, req)
    if table_id != table_id2:
        return Error500().get()

    restaurant, status_code = get_restaurant_table(restaurant_id, table_id)
    if status_code == 200:
        return restaurant, 200
    else: # unexpected error
        return Error500().get()

def delete_restaurant_table(restaurant_id, table_id):
    """ Delete the restaurant table specified by the id.

    DELETE /restaurants/{restaurant_id}/tables/{table_id}
    
    Deletion is only possible if the restaurant has not yet passed.

    Otherwise it remains stored (necessary for contact tracing)

    Status Codes:
        204 - Deleted
        404 - Restaurant not found
        409 - The table has pending reservations, those must be deleted first
        500 - Error with the database or the other bookings service
    """
    q = db.session.query(Table).filter(Table.id == table_id and Table.restaurant_id == restaurant_id).first()
    if q is None:
        return Error404("Restaurant or Table not found").get()

    array,code = get_future_bookings(restaurant_id, table_id)
    if code != 200:
        return Error500().get() # Cannot connect to the bookings service

    if len(array) != 0:
        return Error409("The table has pending reservations, those must be deleted first").get()

    if not del_table(table_id):
        return Error500().get() # DB error

    return NoContent, 204


def get_config(configuration=None):
    """ Returns a json file containing the configuration to use in the app

    The configuration to be used can be passed as a parameter, 
    otherwise the one indicated by default in config.ini is chosen

    ------------------------------------
    [CONFIG]
    CONFIG = The_default_configuration
    ------------------------------------

    Params:
        - configuration: if it is a string it indicates the configuration to choose in config.ini
    """
    try:
        parser = configparser.ConfigParser()
        if parser.read('config.ini') != []:
            
            if type(configuration) != str: # if it's not a string, take the default one
                configuration = parser["CONFIG"]["CONFIG"]

            logging.info("- GoOutSafe:Restaurants CONFIGURATION: %s",configuration)
            configuration = parser._sections[configuration] # get the configuration data

            parsed_configuration = {}
            for k,v in configuration.items(): # Capitalize keys and translate strings (when possible) to their relative number or boolean
                k = k.upper()
                parsed_configuration[k] = v
                try:
                    parsed_configuration[k] = int(v)
                except:
                    try:
                        parsed_configuration[k] = float(v)
                    except:
                        if v == "true":
                            parsed_configuration[k] = True
                        elif v == "false":
                            parsed_configuration[k] = False

            for k,v in DEFAULT_CONFIGURATION.items():
                if not k in parsed_configuration: # if some data are missing enter the default ones
                    parsed_configuration[k] = v

            return parsed_configuration
        else:
            return DEFAULT_CONFIGURATION
    except Exception as e:
        logging.info("- GoOutSafe:Restaurants CONFIGURATION ERROR: %s",e)
        logging.info("- GoOutSafe:Restaurants RUNNING: Default Configuration")
        return DEFAULT_CONFIGURATION

def setup(application, config):

    if config["REMOVE_DB"]: # remove the db file
        logging.info("- GoOutSafe:Restaurants Removing Database...")
        try:
            os.remove("restaurants/"+config["SQLALCHEMY_DATABASE_URI"])
            logging.info("- GoOutSafe:Restaurants Database Removed")
        except:
            pass

    config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"+config["SQLALCHEMY_DATABASE_URI"]

    for k,v in config.items():
        application.config[k] = v # insert the requested configuration in the app configuration

    db.init_app(application)

    if config["DB_DROPALL"]: #remove the data in the db
        logging.info("- GoOutSafe:Restaurants Dropping All from Database...")
        db.drop_all(app=application)

    db.create_all(app=application)

    if config["FAKE_DATA"]: #add fake data (for testing)
        logging.info("- GoOutSafe:Restaurants Adding Fake Data...")
        with application.app_context():
            put_fake_data()

def create_app(configuration=None):
    if configuration is None:
        configuration = os.getenv("CONFIG", "TEST")
    logging.basicConfig(level=logging.INFO)

    app = connexion.App(__name__)
    app.add_api('./swagger.yaml')
    # set the WSGI application callable to allow using uWSGI:
    # uwsgi --http :8080 -w app
    application = app.app

    conf = get_config(configuration)
    logging.info(conf)
    logging.info("- GoOutSafe:Restaurants ONLINE @ ("+conf["IP"]+":"+str(conf["PORT"])+")")
    with app.app.app_context():
        setup(application, conf)

    init_celery(application)

    return app

def create_worker_app():
    configuration = os.getenv("CONFIG", "TEST")
    logging.basicConfig(level=logging.INFO)

    app = connexion.App(__name__)
    app.add_api('./swagger.yaml')
    # set the WSGI application callable to allow using uWSGI:
    # uwsgi --http :8080 -w app
    application = app.app

    conf = get_config(configuration)
    for k,v in conf.items():
        application.config[k] = v # insert the requested configuration in the app configuration

    application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + application.config["SQLALCHEMY_DATABASE_URI"]
    
    db.init_app(application)
    init_celery(application)

    return application

if __name__ == '__main__':

    c = None
    if len(sys.argv) > 1: # if it is inserted
        c = sys.argv[1] # get the configuration name from the arguments

    app = create_app(c)

    with app.app.app_context():
        app.run(
            host=current_app.config["IP"], 
            port=current_app.config["PORT"], 
            debug=current_app.config["DEBUG"]
            )