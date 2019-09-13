###################################
## This module supplies utility functions useful for processing fetched data from Jira.
##
###################################
import time
import collections
import math
from datetime import date
from datetime import timedelta 

class ProcessingUtils():
    name = 'Jira Processing'

    def create_sum_of_story_point_field(self, issues):
        """ This function takes a list of issues and summarize the values in the field customfield_10003(Story Point).

            Arguments:
                issues: JIRA module return data from 'search_issues' function.
        """
        valueList = []
        
        for issue in issues:
            if hasattr(issue.fields, 'customfield_10003'):
                if isinstance(issue.fields.customfield_10003, float):
                    valueList.append(float(issue.fields.customfield_10003))
        aggregatedValue = sum(valueList)
        return aggregatedValue
    
    def create_sum_of_story_point_field_excl_epic(self, issues):
        """ This function takes a list of issues and summarize the values in the field customfield_10003(Story Point). Issue type Epic are ignored.

            Arguments:
                issues: JIRA module return data from 'search_issues' function.
        """
        valueList = []
        
        for issue in issues:
            if hasattr(issue.fields, 'customfield_10003'):
                if (issue.fields.issuetype.name != 'Epic'):
                    if isinstance(issue.fields.customfield_10003, float):
                        valueList.append(float(issue.fields.customfield_10003))
        aggregatedValue = sum(valueList)
        return aggregatedValue
    
    def create_sum_of_original_estimate_field(self, issues):
        """ This function takes a list of issue and summarize the values in the field timeoriginalestimate (timeoriginalestimate.)

            Arguments:
                issues: JIRA module return data from 'search_issues' function.
        """
        valueList = []
        
        for issue in issues:
            if hasattr(issue.fields, 'timeoriginalestimate'):
                if isinstance(issue.fields.timeoriginalestimate, int):
                    valueList.append(float(issue.fields.timeoriginalestimate))
        aggregatedValue = sum(valueList)
        return aggregatedValue
    
    def get_sizing(self, issues, department):
        """ This function takes a list of issue and summarize the values in the field sizing field for the particular department customfield_12003(sws sizing)

            Arguments:
                issues: JIRA module return data from 'search_issues' function.
                department: string (name of department)
        """
        department = department.lower();
        # the if could properly be made smarter.. but did not look into EMUN.
        if department in ['aes']:
            depStr = ['customfield_12307','customfield_12002']
        elif department in ['aes aud feature']:
            depStr = ['customfield_12002']
        elif department in ['aes conn feature']:
            depStr = ['customfield_12307']
        elif department in ['hw']:
            depStr = ['customfield_12304']
        elif department in ['set']:
            depStr = ['customfield_12502']
        elif department in ['siv']:
            depStr = ['customfield_12302']
        elif department in ['sws']:
            depStr = ['customfield_12003']
        elif department in ['it']:
            depStr = ['customfield_13700']
        elif department in ['se']:
            depStr = ['customfield_12303']
        elif department in ['total','hig']:
            #depStr = ['customfield_12042']
            depStr = ['customfield_13700','customfield_12307','customfield_12002','customfield_12002','customfield_12307','customfield_12304','customfield_12502','customfield_12302','customfield_12003']

        else:
            raise NameError('Department: ' + department + ' not found...')
        
        valueList = []
        
        if not(isinstance(issues, collections.Iterable)):
            issues = [issues];
        
        
        
        for issue in issues:
            for dep in depStr:
                if hasattr(issue.fields, dep):
                    temp = eval('issue.fields.'+dep);
                    if isinstance(temp, float):
                        valueList.append(temp);
                        
        if not valueList:
            aggregatedValue = float('NaN');
        else:
            aggregatedValue = sum(valueList);
            
        return aggregatedValue  
    
    def get_two_week_sprint_name(self, timeStruct):
        """ timeInSec = Some time in the sprint assuming sprint starts at monday"""
    
        weekDay = date.weekday(timeStruct)
        weekNumber = date.isocalendar(timeStruct)[1]
        
        if (weekNumber & 1) == 1: # odd weekNumber
            sprintName = timeStruct.strftime("%y")+"W"+str(weekNumber).zfill(2);
            sprintStartDate = timeStruct + timedelta(days=-weekDay)
            sprintEndDate = timeStruct + timedelta(weeks=2,days=-weekDay)
            
        else: # even weekNumber
            tempTimeStruct = timeStruct + timedelta(weeks=-1)
            year = date.isocalendar(tempTimeStruct)[0]
            sprintName = str(year)[-2]+str(year)[-1]+"W"+str(date.isocalendar(tempTimeStruct)[1]).zfill(2) # subtracting a week to make sprint name
            sprintStartDate = tempTimeStruct + timedelta(days=-weekDay)
            sprintEndDate = tempTimeStruct + timedelta(weeks=2,days=-weekDay)
        
        sprintStart = sprintStartDate.strftime("%Y/%m/%d 12:00") #'yyyy/mm/dd 12:00'
        sprintEnd = sprintEndDate.strftime("%Y/%m/%d 12:00") #'yyyy/mm/dd 12:00'
    
        return sprintName, sprintStart, sprintEnd

    def get_cadence_fixversion_name(self, timeStruct):
        """ timeStruct = Some time in the sprint assuming sprint starts at monday"""

        weekDay = date.weekday(timeStruct)
        weekNumber = date.isocalendar(timeStruct)[1]

        if (weekNumber & 1) == 1:  # odd weekNumber
            timeStruct = timeStruct + timedelta(weeks=1) # first week of sprint added 1 week to get to the biweekly deadline.

        release_date = (timeStruct + timedelta(days=4-weekDay)).strftime("%Y-%m-%d") # setting the release date to friday in the release date week 'yyyy/mm/dd'
        fixversion_name = timeStruct.strftime("%y") + str(date.isocalendar(timeStruct)[1]).zfill(2)

        return fixversion_name, release_date

    def get_one_week_sprint_name(self, timeStruct):
        """ timeInSec = Some time in the sprint assuming sprint starts at monday"""
    
        weekDay = date.weekday(timeStruct)
        weekNumber = date.isocalendar(timeStruct)[1]
        sprintName = timeStruct.strftime("%y")+"W"+str(weekNumber).zfill(2);
        sprintStartDate = timeStruct + timedelta(days=-weekDay)
        sprintEndDate = timeStruct + timedelta(weeks=1,days=-weekDay)
        sprintStart = sprintStartDate.strftime("%Y/%m/%d 12:00") #'yyyy/mm/dd 12:00'
        sprintEnd = sprintEndDate.strftime("%Y/%m/%d 12:00") #'yyyy/mm/dd 12:00'
        
        return sprintName, sprintStart, sprintEnd
    
    def search_issues_all(self, jira_session, jqlStr, validate_query, fields, expand, json_result):
        """ the default search will not return more than 1000 items. This one return them all."""
      
        startAt = 0;
        maxResults = 1000;
        searchBasics = jira_session.search_issues(jqlStr,
                                             startAt=startAt,
                                             maxResults=1,
                                             validate_query=validate_query,
                                             fields=fields,
                                             expand=expand, # read i.e. description as html code.
                                             json_result=json_result)
        items = [];
        
        for idx in range(0, math.ceil(searchBasics.total/maxResults)):
    
            searchResult = jira_session.search_issues(jqlStr,
                                             startAt=(maxResults*idx),
                                             maxResults=maxResults,
                                             validate_query=validate_query,
                                             fields=fields,
                                             expand=expand, # read i.e. description as html code.
                                             json_result=None)    

            items = items + searchResult
            
        return items