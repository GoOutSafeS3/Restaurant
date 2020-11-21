from celery import Celery
from celery.schedules import crontab
from restaurants.orm import db,Rating,Restaurant
from celery.utils.log import get_task_logger
import datetime

logger = get_task_logger(__name__)

celery = Celery()
_APP = None

@celery.task
def recompute_ratings():
    """ This task recompute all the rating for all the restaurants.
        The other task has numerical instability so may report wrong ratings long time. """
    with _APP.app_context():
        try:
            ratings = db.session.query(Rating).filter().all() # All the ratings
            rests_rating = {} # A dictionary containings for every restaurant the sum of the rating received and the number

            for rate in ratings:
                sum,num = rests_rating.get(rate.restaurant_id, (0,0))
                rests_rating[rate.restaurant_id] = (sum+rate.rating, num+1)
                rate.marked = True # This task still mark the ratings

            for rest_id,(sum,num) in rests_rating.items():
                rest = db.session.query(Restaurant).filter(Restaurant.id == rest_id).first()
                rest.rating_val = sum/num # Mean rating for every restaurant
                rest.rating_num = num
        except: # pragma: no cover
            traceback.print_exc()
            logger.info("task-recompute-rollback")
            db.session.rollback()
            raise
        else:
            logger.info("task-recompute-commit")
            db.session.commit()
import traceback


@celery.task
def check_ratings():
    """ This task compute the new mean rating for the restaurants that have unmarked ratings """
    with _APP.app_context():
        try:
            ratings = db.session.query(Rating).filter(Rating.marked == False).all()
            for rate in ratings:
                val = rate.restaurant.rating_val
                num = rate.restaurant.rating_num
                rate.restaurant.rating_val = (val*num + rate.rating) / (num+1)
                rate.restaurant.rating_num += 1
                rate.marked = True
        except:
            traceback.print_exc()
            logger.info("task-check_ratings-rollback")
            db.session.rollback()
            raise
        else:
            logger.info("task-check_ratings-commit")
            db.session.commit()

@celery.task
def log(message):
    logger.debug(message)
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

def init_celery(app, worker=False):
    #print(app.config,flush=True)
    # load celery config
    celery.config_from_object(app.config)
    global _APP
    _APP = app
    if not worker:
        # Config for non-worker related settings
        pass