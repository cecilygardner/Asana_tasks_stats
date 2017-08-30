Asana request metrics pulls task data from a specified project and creates a new
Asana task with metrics associated with the project. The script defaults to pulling
task data for the last 30 days (though that can be overridden via the argparser
to pull for a date range) in a specified project. The script then filters out
incomplete tasks and sections. The following calculations from the task set
are added to a new asana task created in a specified project:
* mean close time
* medium
* 1 std below and above
* list of tasks 1 std below the mean
* list of tasks 1 std above the mean

Note:
* close time means the time in days between task creation and task completion
* the project to pull from, the project to create the task in, and the Asana
api connection information (PID & user ID) are specified in the asana_config.json
file