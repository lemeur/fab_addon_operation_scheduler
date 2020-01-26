import logging
from flask_appbuilder.basemanager import BaseManager
from flask_babel import lazy_gettext as _
from flask import Blueprint, url_for
from werkzeug.serving import is_running_from_reloader

from .views import ScheduledOperationView, SchedulerManagerView
from .addon_scheduler import AddonScheduler, SCHEDULER_TIMEZONE, SCHEDULER_SELFCHECK_INTERVAL, scheduler_selfcheck

#from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from multiprocessing import Value

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

    SCHEDULER_API_ENABLED = False


class OperationSchedulerManager(BaseManager):
    last_check = None

    def __init__(self, appbuilder):
        """
             Use the constructor to setup any config keys specific for your app. 
        """
        super(OperationSchedulerManager, self).__init__(appbuilder)
        app = self.appbuilder.get_app
        app.config.from_object(Config())

        self.static_bp = Blueprint('fab_addon_operation_scheduler', __name__,
                                   url_prefix='/fab_addon_operation_scheduler',
                                   template_folder='templates/fab_addon_operation_scheduler',
                                   static_folder='static/fab_addon_operation_scheduler')
        self.addon_js = [('fab_addon_operation_scheduler.static', 'js/main.js')]
        self.addon_css = []

        # Define the new scheduler: a singleton
        if is_running_from_reloader():
            log.debug("Running from Reloader: not starting scheduler again")
        else:
            log.debug("Instantiating scheduler (if not already instanciated)")
            schedulerObj = AddonScheduler(appbuilder)
            self.addon_scheduler = schedulerObj

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
        pass

