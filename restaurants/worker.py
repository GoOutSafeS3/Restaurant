from celery import Celery
from celery.schedules import crontab

from restaurants.app import create_worker_app
from restaurants.background import check_ratings, recompute_ratings

def create_celery(app):

    celery = Celery(
        app.import_name,
        backend=app.config["result_backend"],
        broker=app.config["broker_url"],
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


app = create_worker_app()
celery = create_celery(app)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    
    sender.add_periodic_task(float(app.config["COMMIT_RATINGS_AFTER"]), check_ratings.s(), name=f"Mark likes and add to respective restaurants | a controll each {app.config['UNMARK_AFTER']} seconds")

    # Executes every monday morning at 4:30 a.m. see https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html#crontab-schedules
    sender.add_periodic_task(
        crontab(minute=30, hour=4, day_of_week=1), recompute_ratings.s(),
    )