####################################################################################################
##
## This program creates a design review page tailored for the Team Toolbox Gearbox releases
##
####################################################################################################
import confluence
import datetime
#JIRA
import jira_utils
import jira.client
# Commandline options
import json
import sys


def get_jira_client():
    """ The minimal set to get access to JIRA """
    """ Example data - see jiraOAuth.json and jiraOptions.json for actually used values."""

    jira_connection = jira_utils.Client(jsonOAuthFile="./jiraOAuth.json", jsonOptionsFile="./jiraOptions.json")
    #print("Connected to JIRA server. Data returned:")
    #print(jira_connection.server_info())
    return jira_connection


def get_confluence_client(spacekey):
    """ The minimal setup to get access to Confluence """
    with open('./key_cert_wdh.pem', "r") as key_cert_file:
        key_cert_data = key_cert_file.read()

    oauth_data = {
        'access_token': '<ACCESS TOKEN>',
        'access_token_secret': '<ACCESS TOKEN SECRET>',
        'consumer_key': '<CONSUMER KEY>',
        'consumer_secret': '<CONSUMER SECRET>',
        'key_cert': key_cert_data,
    }
    options = {
        'server': 'http://<CONFLUENCE URL>',
        'spacekey': spacekey
    }
    return confluence.Client(oauth=oauth_data, options=options)


def create_design_review_page(config, variables):
    jira_session = get_jira_client()
    
    if 'spacekey' in config:
        spacekey = config['spacekey']
    else:
        spacekey = "<TEST SPACE KEY>"
    confluence_session = get_confluence_client(spacekey)
    confluence_utils = confluence.ContentUtils(confluence_session)

    release = variables['RELEASE_VERSION']
    date = variables['REVIEW_DATE']

    # Build tables from JIRA queries
    titles = "Key,T,Summary,Status,Resolution,Reviewers,Reviews"
    fields = "key,type,summary,status,resolution,customfield_11400,customfield_11402"
    jql_str = 'project=GEAR AND type=Story AND resolution NOT IN ("Won\'t Fix", "Won\'t Do", "Duplicate") AND fixVersion=' + release
    story_issues = jira_session.search_issues(jql_str,
                                              startAt=0,
                                              maxResults=100,
                                              validate_query=True,
                                              fields=fields,
                                              expand="renderedFields",
                                              json_result=None)

    story_table = confluence_utils.create_jira_issue_table(story_issues, fields, titles).decode('UTF-8')

    jql_str = 'project=GEAR AND type=Bug AND fixVersion=' + release
    bug_issues = jira_session.search_issues(jql_str,
                                            startAt=0,
                                            maxResults=100,
                                            validate_query=True,
                                            fields=fields,
                                            expand="renderedFields",
                                            json_result=None)
    bug_table = confluence_utils.create_jira_issue_table(bug_issues, fields, titles).decode('UTF-8')

    variables['BUGS_DONE_TABLE'] = bug_table
    variables['STORIES_DONE_TABLE'] = story_table

    # Generate the page
    content = confluence_utils.generate_page_from_template(parent_page_id=config['parent_page_id'],
                                                           template_page_id=config['template_page_id'],
                                                           title="Design Review - Release "+release,
                                                           substitutions=variables)
    
    created_page_id = confluence_utils.get_page_id(content)
    # The label in the template does not get propagated to the page instances
    # Therefore we need to add that label manually
    confluence_utils.set_labels(page_id=created_page_id, labels=["design-review"])
    
    return content


def generate_test_data():
    release = "4.1.0"
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    variables = {
                'REVIEW_DATE': date,
                'RELEASE_VERSION': release
                }
    return variables

# This method takes a byte array-representation of a JSON dictionary, as received from the confluence call.
# The method extracts relevant data and prints the output or throws exception in case the status is an error.
def print_status(status):
    status = json.loads(status.decode('UTF-8'));
    if "statusCode" in status:
        if 'statusCode' in status and 'message' in status:
            raise RuntimeError("Design Review was not created!\nStatusCode="+str(status['statusCode']) + ", " + status['message'])
        else:
            raise RuntimeError("Design Review was not created!")
    else:
        if 'title' in status and 'space' in status and 'key' in status['space']:
            print("Design Review created successfully with title " + status['title'] + " in space " + status['space']['key'])
        else:
            print("Design Review created successfully");

# Create a design review
if __name__ == "__main__":
    # The program takes exactly one argument:
    #  A json file containing two dictionaries, configuring the program page ids, and variables for the page.
    # Argument check
    if len(sys.argv) < 2:
        print(sys.argv[0] + ' <json file>')
        print('The json file must be formatted like this:"')
        print('{')
        print('  config":{')
        print('    "template_page_id" : 61210645,')
        print('    "parent_page_id"   : 61210633,')
        print('    "test_mode"        : 0, (optional, only used for test)')
        print('    "spacekey"        : "<SPACEKEY>"')
        print('  },')
        print('  variables": {')
        print('    "REVIEW_DATE": "2017-03-02 22:49:14",')
        print('    "RELEASE_VERSION": "4.1.0"')
        print('  }')
        print('}')
        sys.exit(1)

    fp = open(sys.argv[1], "r")
    data = json.load(fp)
    if 'test_mode' in data['config'] and data['config']['test_mode']:
        data['variables'] = generate_test_data()

    print("Creating a new design review page for release %s" % data['variables']['RELEASE_VERSION'])
    status = create_design_review_page(config=data['config'], variables=data['variables'])
    
    print_status(status)