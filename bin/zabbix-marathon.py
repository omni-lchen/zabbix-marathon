#!/usr/bin/env python

# Date:        17/08/2016
# Author:      Long Chen
# Description: A script to send marathon docker container metrics data by using python zabbix sender
# Requires Python Zabbix Sender: https://github.com/kmomberg/pyZabbixSender/blob/master/pyZabbixSender.py
# Example Usage: zabbix-marathon.py <marathon server ip address> <marathon app id> <zabbix host name> <marathon_user_name> <marathon_user_password>

from pyZabbixSender import pyZabbixSender
from datetime import datetime
import time
import json
import urllib2
import base64
import sys

class zabbixMarathon(object):
    def __init__(self, marathon_server, marathon_app_id, zabbix_host, marathon_user_name, marathon_user_password):
        self.marathon_server = marathon_server
        self.marathon_app_id = marathon_app_id
        self.marathon_user_name = marathon_user_name
        self.marathon_user_password = marathon_user_password
        self.zabbix_server = '127.0.0.1'
        self.zabbix_host = zabbix_host
        self.__metrics = []

    def add_metrics(self, k, v):
        dict_metrics = {}
        dict_metrics['key'] = k
        dict_metrics['value'] = v
        self.__metrics.append(dict_metrics)

    def getMarathonAppMetrics(self):
        marathon_server_url = 'http://' + self.marathon_server + ':8080/v2/apps' + self.marathon_app_id + '?embed=app.taskStats'
        try:
            # Basic authentication with marathon server
            api_request = urllib2.Request(marathon_server_url)
            base64string = base64.encodestring('%s:%s' % (self.marathon_user_name, self.marathon_user_password)).replace('\n', '')
            api_request.add_header("Authorization", "Basic %s" % base64string)
            api_response = urllib2.urlopen(api_request, timeout=10)
            result = json.load(api_response)
            number_of_tasks_running = result['app']['tasksRunning']
            self.add_metrics('marathon.app.tasks.running', number_of_tasks_running)
            number_of_tasks_healthy = result['app']['tasksHealthy']
            self.add_metrics('marathon.app.tasks.healthy', number_of_tasks_healthy)
            # Containers data used discovery
            lldlist = []
            dict_metrics = {}
            dict_metrics['key'] = 'marathon.app.containers.discovery'
            dict_metrics['value'] = {"data": lldlist}
            # Marathon app tasks
            tasks = result['app']['tasks']
            for task in tasks:
                # Add containers discovery
                host = task['host']
                slaveId = task['slaveId']
                llddict = {}
                llddict["{#HOST}"]  = host
                llddict["{#SLAVEID}"] = slaveId
                lldlist.append(llddict)
                # Get marathon task state
                task_state = task['state'] # TASK_RUNNING, TASK_LOST
                if task_state == 'TASK_RUNNING':
                    task_state = 1
                else:
                    task_state = 0
                # Get container start time
                startTime = task['startedAt']
                # Get container health status
                if 'healthCheckResults' in task:
                    # true or false
                    alive = task['healthCheckResults'][0]['alive']
                    if alive:
                        runningState = 1
                    else:
                        runningState = 0
                else:
                    runningState = 0
                # Add container metrics
                zabbix_item_key = 'task_state[' + host + ',' + slaveId + ']'
                zabbix_item_key_value = task_state
                self.add_metrics(zabbix_item_key, zabbix_item_key_value)
                zabbix_item_key = 'start_time[' + host + ',' + slaveId + ']'
                zabbix_item_key_value = time.mktime((datetime.strptime(startTime[:-5], "%Y-%m-%dT%H:%M:%S")).timetuple())
                self.add_metrics(zabbix_item_key, zabbix_item_key_value)
                zabbix_item_key = 'container_state[' + host + ',' + slaveId + ']'
                zabbix_item_key_value = runningState
                self.add_metrics(zabbix_item_key, zabbix_item_key_value)
            self.__metrics.insert(0, dict_metrics)
        except urllib2.HTTPError as e:
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
            sys.exit(1)
        except urllib2.URLError as e:
            print 'Reach the server failing.'
            print 'Reason: ', e.reason
            sys.exit(1)

    def sendMetrics(self):
        # Init zabbix sender to connect to zabbix server
        zabbix_sender = pyZabbixSender(server=self.zabbix_server, port=10051)
        metrics = self.__metrics
        for metric in metrics:
            zabbix_item_key = str(metric['key'])
            zabbix_item_value = str(metric['value'])
            zabbix_sender.addData(zabbix_host,zabbix_item_key,zabbix_item_value)
        #zabbix_sender.printData()
        result = zabbix_sender.sendData()
        print result[0][0]

if __name__ == '__main__':
    # Get marathon server from command line argument
    marathon_server = str(sys.argv[1])
    marathon_app_id = str(sys.argv[2])
    zabbix_host = str(sys.argv[3])
    marathon_user_name = str(sys.argv[4])
    marathon_user_password = str(sys.argv[5])
    zabbixMarathon = zabbixMarathon(marathon_server, marathon_app_id, zabbix_host, marathon_user_name, marathon_user_password)
    zabbixMarathon.getMarathonAppMetrics()
    zabbixMarathon.sendMetrics()
