from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from datetime import datetime

import logging
log = logging.getLogger(__name__)

SCHEDULER_TIMEZONE="Europe/Paris"
SCHEDULER_SELFCHECK_INTERVAL=30

def scheduler_selfcheck():
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    AddonScheduler.set_last_check(now)
    log.debug("fab_addon_operation_scheduler selfcheck:{}".format(now))

class AddonScheduler(object):
    __instance = None
    last_check = None

    def __new__(cls, appbuilder, external_scheduler=None):
        if appbuilder.fab_addon_operation_scheduler_started.value:
            log.debug("APScheduler: Scheduler ALREADY instantiated")
            return AddonScheduler.__instance
            
        if AddonScheduler.__instance is None:
            log.debug("APScheduler: Instanciating NEW Scheduler")
            AddonScheduler.__instance = object.__new__(cls)
            if external_scheduler and isinstance(external_scheduler,APScheduler):
                log.debug("APScheduler: using the provided scheduler")
                AddonScheduler.__instance.scheduler = external_scheduler
                appbuilder.fab_addon_operation_scheduler_started.value = True
            else:
                log.debug("APScheduler: instantiating a new BackgroundScheduler")
                bgsched = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE, daemon=True) 
                scheduler = APScheduler(scheduler=bgsched)
                scheduler.init_app(appbuilder.get_app)
                AddonScheduler.__instance.scheduler = scheduler
                appbuilder.fab_addon_operation_scheduler_started.value = True
        else:
                log.debug("APScheduler: Instance ALREADY instanted")
        # when creating new scheduler, delete all jobs, they'll be reloaded from DB
        AddonScheduler.__instance.scheduler.remove_all_jobs()
        return AddonScheduler.__instance

    def __del__(self):
        log.debug("Deleting Scheduler")
        AddonScheduler.__instance.scheduler.shutdown(wait=False)

    @classmethod
    def set_last_check(cls, datestamp):
        cls.last_check = datestamp

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

    @classmethod
    def remove_all_jobs(cls):
        return cls.__instance.scheduler.remove_all_jobs()
