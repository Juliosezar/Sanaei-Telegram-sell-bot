from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def my_scheduled_job():
    # Your task logic here
    logger.info("Running my scheduled job")

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Schedule job every 50 seconds
    scheduler.add_job(my_scheduled_job, trigger=IntervalTrigger(seconds=50), id="my_scheduled_job", replace_existing=True)

    register_events(scheduler)
    scheduler.start()
    logger.info("Scheduler started")

    # Shut down the scheduler when exiting the app
    import atexit
    atexit.register(lambda: scheduler.shutdown())
