import logging
#from flask.ext.appbuilder.basemanager import BaseManager
from flask_appbuilder.basemanager import BaseManager
from flask_babel import lazy_gettext as _
from .views import ScheduledOperationView

from .models import ListOfOperations, SchedulableOperation

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
        'default': SQLAlchemyJobStore(url='sqlite:///fab_addon_operation_scheduler.db')
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
        dbsession = appbuilder.get_session()
        dbsession.query(SchedulableOperation).delete()
        dbsession.commit()

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
        bgsched = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE, daemon=True)
        scheduler = APScheduler(scheduler=bgsched)
        scheduler.init_app(self.appbuilder.get_app)
        scheduler.start()

        if scheduler.get_job('selfcheck'):
            scheduler.remove_job('selfcheck')
        scheduler.add_job('selfcheck', scheduler_selfcheck, trigger='interval', seconds=SCHEDULER_SELFCHECK_INTERVAL, max_instances=6, misfire_grace_time=SCHEDULER_SELFCHECK_INTERVAL)



    def post_process(self):
        pass

def scheduler_selfcheck():
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    OperationSchedulerManager.set_last_check(now)
    #print("TIBO SCHEDULER SELFCHECK:",OperationSchedulerManager.get_last_check())
    #print("TIBO SCHEDULER LISTCHECK:",ListOfOperations.get_all())

