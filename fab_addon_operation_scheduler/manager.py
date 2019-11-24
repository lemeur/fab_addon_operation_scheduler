import logging
from flask_appbuilder.basemanager import BaseManager
from flask_babel import lazy_gettext as _

addon_instance = None

from .views import ScheduledOperationView
from .models import SchedulableOperation

#from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from datetime import datetime

log = logging.getLogger(__name__)


"""
   Create your plugin manager, extend from BaseManager.
   This will let you create your models and register your views
   
"""


SCHEDULER_TIMEZONE="Europe/Paris"
SCHEDULER_SELFCHECK_INTERVAL=30

class Config(object):
    JOBS = [
    ]

    SCHEDULER_JOBSTORES = {
#        'default': SQLAlchemyJobStore(url='sqlite:///fab_addon_operation_scheduler.db')
         'default': MemoryJobStore()
    }

    SCHEDULER_API_ENABLED = True


class OperationSchedulerManager(BaseManager):
    last_check = None

    def __init__(self, appbuilder):
        """
             Use the constructor to setup any config keys specific for your app. 
        """
        super(OperationSchedulerManager, self).__init__(appbuilder)
        self.appbuilder.get_app.config.from_object(Config())

        # Delete all SchedulableOperation at startup, 
        # they will be registered programmatically by calling
        # ListOfOperations.register_operation()
        log.debug("APScheduler: removing SchedulableOperation")
        dbsession = appbuilder.get_session()
        dbsession.query(SchedulableOperation).delete()
        dbsession.commit()
        self.dbsession = dbsession

        # Since the JobStore is not persistent we don't
        # have to empty the JobStore (MemoryJobStore)

        # Define the new scheduler
        log.debug("APScheduler: defining BackgroundScheduler")
        bgsched = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE, daemon=True)
        scheduler = APScheduler(scheduler=bgsched)
        scheduler.init_app(self.appbuilder.get_app)
        self.scheduler = scheduler

        addon_instance = self

    @classmethod
    def set_last_check(cls, datestring):
        cls.last_check = datestring

    @classmethod
    def get_last_check(cls):
        return cls.last_check

    def register_views(self):
        """
            This method is called by AppBuilder when initializing, use it to add you views
        """
        self.appbuilder.add_view(ScheduledOperationView, "Schedulable_Operations",icon = "fa-user",category = "Scheduler")

    def pre_process(self):
        pass

    def post_process(self):

        # Run the scheduler
        log.debug("APScheduler: starting scheduler")
        self.scheduler.start()

        #log.debug("APScheduler: adding selfcheck task")
        selfcheck_job = self.scheduler.get_job('selfcheck')
        if selfcheck_job:
            selfcheck_job.remove()
        self.scheduler.add_job('selfcheck', scheduler_selfcheck, trigger='interval', seconds=SCHEDULER_SELFCHECK_INTERVAL, max_instances=6, misfire_grace_time=SCHEDULER_SELFCHECK_INTERVAL)

        # Reload ScheduledOperations
        # ==> This can't be done at this time
        # because functions may have not been registered yet.
        # ==> This will be done at registration time

def scheduler_selfcheck():
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    OperationSchedulerManager.set_last_check(now)
    log.debug("fab_addon_operation_scheduler selfcheck:{}".format(now))

