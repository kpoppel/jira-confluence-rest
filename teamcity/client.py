import json
import requests

##################################################################################
# Python Interface for Confluence, supporting a subset of the full REST interface.
#
# Written for the purpose of allowing commandline updates to Confluence pages.
# This module tries to be as clean as possible and only provide REST functions.
##################################################################################

class Client:
    _headers = {'Content-Type': 'application/json',
                'Accept': 'application/json'}
    
    _guestServerUrl = "http://<MY TEAMCITY INSTANCE>/guestAuth/app/rest/"


          
    def getBuild(self, buildID):
        
        uri = self._guestServerUrl+"builds?locator=buildType:(id:" + buildID + "),running:any&fields=count,build(status)"
        resp = requests.get(uri, headers=self._headers)
        data = json.loads(resp.content.decode("utf-8"))
        return data['build']
           
    
    def getLatestProjectBuilds(self, projectID):
        
        uri = self._guestServerUrl+"buildTypes?locator=affectedProject:(id:"+ projectID+")&fields=buildType(id,name,builds($locator(running:false,canceled:false,count:1),build(number,status,statusText)))"
        
        resp = requests.get(uri, headers=self._headers)
        data = json.loads(resp.content.decode("utf-8"))
        return data['buildType']
    
    def getLatestBuild(self, buildID):
        
        uri = self._guestServerUrl+"buildTypes/id:"+ buildID+"/builds?count=1"
        resp = requests.get(uri, headers=self._headers)
        data = json.loads(resp.content.decode("utf-8"))
        return data['build']
    
    def getProjectBuilds(self, projectID):
        
        uri = self._guestServerUrl+"projects/id:" + projectID        
        resp = requests.get(uri, headers=self._headers)
        data = json.loads(resp.content.decode("utf-8"))
        buildtype = data['buildTypes'];
        buildtype = data['buildTypes'];
        return buildtype['buildType']
