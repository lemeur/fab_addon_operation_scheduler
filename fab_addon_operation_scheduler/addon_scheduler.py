from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

import logging
log = logging.getLogger(__name__)

SCHEDULER_TIMEZONE="Europe/Paris"
SCHEDULER_SELFCHECK_INTERVAL=30

class AddonScheduler(object):
    __instance = None

    def __new__(cls, appbuilder, external_scheduler=None):
        if AddonScheduler.__instance is None:
            AddonScheduler.__instance = object.__new__(cls)
        if external_scheduler and isinstance(external_scheduler,APScheduler):
            log.debug("APScheduler: using the provided scheduler")
            AddonScheduler.__instance.scheduler = external_scheduler
        else:
            log.debug("APScheduler: instantiating a new BackgroundScheduler")
            bgsched = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE, daemon=True) 
            scheduler = APScheduler(scheduler=bgsched)
            scheduler.init_app(appbuilder.get_app)
            AddonScheduler.__instance.scheduler = scheduler
        return AddonScheduler.__instance

    @classmethod
    def get_scheduler(cls):
        return cls.__instance.scheduler

    @classmethod
    def start(cls):
        cls.__instance.scheduler.start()

    @classmethod
    def add_job(cls, jobid, jobfunction, **kwargs):
        return cls.__instance.scheduler.add_job(jobid, jobfunction, **kwargs)

    @classmethod
    def get_job(cls, jobid):
        return cls.__instance.scheduler.get_job(jobid)
