from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
import datetime

db = SQLAlchemy()

class Restaurant(db.Model):

    __tablename__ = 'restaurant'
    __table_args__ = {'sqlite_autoincrement':True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    name = db.Column(db.Text(100))
    rating_val = db.Column(db.Float, default=0) # will store the mean value of the rating
    rating_num = db.Column(db.Integer, default=0) # will store the number of ratings
    lat = db.Column(db.Float) # restaurant latitude
    lon = db.Column(db.Float) # restaurant longitude
    first_opening_hour = db.Column(db.Integer) # the opening hour for the first opening
    first_closing_hour = db.Column(db.Integer) # the closing hour for the first opening
    second_opening_hour = db.Column(db.Integer) # the opening hour for the second opening
    second_closing_hour = db.Column(db.Integer) # the closing hour for the second opening
    occupation_time = db.Column(db.Integer) # in hours the time of occupation of a table
    closed_days = db.Column(db.Text(7), default="") # one number for every closing day (1-7 i.e. monday-sunday)
    phone = db.Column(db.Text(16))
    cuisine_type = db.Column(db.Text(1000))
    menu = db.Column(db.Text(1000))
    tables = relationship('Table')

    def get_id(self):
        return self.id

    def dump(self):
        """ Return a db record as a dict """
        d = dict([(k,v) for k,v in self.__dict__.items() if k[0] != '_'])
        d["closed_days"] = [int(day) for day in d["closed_days"]]
        d["url"] = "/restaurants/"+str(d["id"])
        return d

    def dump_rating(self):
        """ Return a db record as a dict but with only rating and ratings"""
        d = {"rating": self.rating_val, "ratings": self.rating_num}
        return d

class Table(db.Model):
    __tablename__ = 'table'
    __table_args__ = {'sqlite_autoincrement':True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))
    capacity = db.Column(db.Integer)
    restaurant = relationship('Restaurant')

    def dump(self):
        """ Return a db record as a dict """
        d = dict([(k,v) for k,v in self.__dict__.items() if k[0] != '_'])
        d["url"] = "/restaurants/%d/tables/%d" % (d["restaurant_id"],d["id"])
        return d

class Rating(db.Model):
    __tablename__ = 'Rating'
    __table_args__ = {'sqlite_autoincrement':True}
    rater_id = db.Column(db.Integer, primary_key=True, unique=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), primary_key=True)
    restaurant = relationship('Restaurant', foreign_keys='Rating.restaurant_id')
    rating = db.Column(db.Integer)
    marked = db.Column(db.Boolean, default = False) # True iff it has been counted in Restaurant.rating