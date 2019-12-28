import logging
from flask_appbuilder.basemanager import BaseManager
from flask_babel import lazy_gettext as _
from flask import Blueprint, url_for

from .views import ScheduledOperationView, SchedulerManagerView
from .models import SchedulableOperation
from .addon_scheduler import AddonScheduler, SCHEDULER_TIMEZONE, SCHEDULER_SELFCHECK_INTERVAL

#from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from datetime import datetime

log = logging.getLogger(__name__)


"""
   Create your plugin manager, extend from BaseManager.
   This will let you create your models and register your views
   
"""


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

        self.static_bp = Blueprint('fab_addon_operation_scheduler', __name__,
                                   url_prefix='/fab_addon_operation_scheduler',
                                   template_folder='templates/fab_addon_operation_scheduler',
                                   static_folder='static/fab_addon_operation_scheduler')
        self.addon_js = [('fab_addon_operation_scheduler.static', 'js/main.js')]
        self.addon_css = []

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

        # Define the new scheduler: a singleton
        schedulerObj = AddonScheduler(appbuilder)


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
        self.appbuilder.add_view(SchedulerManagerView, "Schedulers",icon = "fa-user",category = "Scheduler")
        self.appbuilder.add_view(ScheduledOperationView, "Schedulable_Operations",icon = "fa-user",category = "Scheduler")

    def pre_process(self):
        log.info("Adding static blueprint for fab_addon_operation_scheduler.")
        self.appbuilder.get_app.register_blueprint(self.static_bp)

    def post_process(self):

        # Run the scheduler
        log.debug("APScheduler: starting scheduler")
        AddonScheduler.start()

        log.debug("APScheduler: adding selfcheck task")
        selfcheck_job = AddonScheduler.get_job('selfcheck')
        if selfcheck_job:
            selfcheck_job.remove()
        AddonScheduler.add_job('selfcheck', scheduler_selfcheck, trigger='interval', seconds=SCHEDULER_SELFCHECK_INTERVAL, max_instances=6, misfire_grace_time=SCHEDULER_SELFCHECK_INTERVAL)

        # Reload ScheduledOperations
        # ==> This can't be done at this time
        # because functions may have not been registered yet.
        # ==> This will be done at registration time

        addon_instance = self
        log.debug("Registered addon_instance with:"+str(addon_instance))

def scheduler_selfcheck():
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    OperationSchedulerManager.set_last_check(now)
    log.debug("fab_addon_operation_scheduler selfcheck:{}".format(now))

