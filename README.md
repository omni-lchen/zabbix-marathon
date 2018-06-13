# zabbix-marathon
Mesos Container monitoring by using Marathon API.

# Metrics
  * marathon.app.tasks.running: number of running tasks
  * marathon.app.tasks.healthy: number of healthy tasks
  * zabbix sender status: 0=OK, 1=Failed
  * container health status: 0=Unhealthy, 1=Healthy
  * container task state: 0=Down, 1=Up
  * container start time

# Prerequisites
  * pyZabbixSender
  
# Installation
  * Import the template into zabbix, tested in version 3.4.x
  * Copy the python scripts to zabbix external scripts directory on zabbix server or proxy: /usr/lib/zabbix/externalscripts
  * Make python scripts executable.
  * Create new zabbix host and link with the template
  * Set up the following macros on the new host:
```
    {$MARATHON_SERVER} -> Server IP
    {$MARATHON_APP_ID} -> /app
    {$USERNAME} -> marathon user login   
    {$PASSWORD} -> marathon user password
```