####################################################################################################
##
## This program updates the AES velocity page: http://confluence.kitenet.com/x/yQDvDw
##
####################################################################################################
import confluence
import datetime
#JIRA
import jira_utils
import json

import jira.client
# Commandline options
import math
import time


from string import Template
import re



# Update Velocity metric confluence page
if __name__ == "__main__":

    jiraAuth = json.load(open("./jiraOAuth.json", "r"))
    jiraOptions = json.load(open("./jiraOptions.json", "r"))
    options = jiraOptions['options']
    options['verify'] = True
    options['timeout'] = None

    jira_session = jira_utils.Client(jsonOAuthFile="./jiraOAuth.json",
                                     options=options)
    print(jira_session)
    print("done...")