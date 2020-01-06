# fab_addon_operation_scheduler
An Flask-Appbuilder scheduler (based on flask-AppScheduler), with graphical UI to schedule tasks

## requirements

This is a plugin for Flask-Appbuilder and must be:
* installed in the virtual environment (```python setup.py install```)
* initialized from within the app configuration as an addon:

In you own app's ```config.py```:
```
ADDON_MANAGERS = ['fab_addon_operation_scheduler.manager.OperationSchedulerManager', 'fab_addon_turbowidgets.manager.TurboWidgetsManager']
```

You can notice that there is a dependancy on another addon: fab_addon_turbowidgets available at [github](https://github.com/lemeur/fab_addon_turbowidgets)

Also, this will require you to update you database, as this addon adds new models

