###################################
## This module supplies utility functions useful for generating pages and page content.
##
###################################
from string import Template
import xml.etree.ElementTree as ET
import json
import time
import datetime
import re

class ContentUtils():
    def __init__(self, client):
        self._client = client

    def set_labels(self, page_id, labels=None):
        self._client.set_labels(page_id=page_id, labels=labels)
        
    def get_page_id(self, content):
        """
        This content comes from the method generate_page_from_template
        It is in a binary format, thus needs to be converted into string
        After that, the page ID can be extracted
        """
        content_decoded_to_string = content.decode("utf-8")
        content_in_json = json.loads(content_decoded_to_string)
        return content_in_json['id']
        

    def generate_page_from_template(self, parent_page_id, template_page_id, title, substitutions):
        """ The way this function works is really simple:
            It replaces any variable name in the received content named $<myvar> with the replacement
            string supplied in an input dictionary. There are more sophisticated template engines out there,
            but this one works well as there is no need to learn yet another templating language to get started.
              It is the client responsibility to generate the proper storage format string.
        """

        parent_page_id = str(parent_page_id)
        template_page_id = str(template_page_id)

        # Get template page
        template_page = self._client.get_page_content(template_page_id)

        # print "TEMPLATE PAGE:\n"+template_page+"\n"
        # substitute
        template = Template(template_page)
        body = template.substitute(substitutions)

        # inject page
        return self._client.create_page(parent_page_id=parent_page_id,
                                title=title,
                                body=body
                                )

    def _field_handler(self, element, field, issue):
        """ Internal service function offering interpretations of a set of known fields.
            Updates the input etree Element tag with the appropriate attributes or string.
        """
        if field == "type":
            # Issuetype:
            #'<a href="https://jira.kitenet.com/browse/' + issue.key + '"><ac:image ac:class="icon" ac:alt="' + type_name + '"><ri:url ri:value="' + type_url + '"/></ac:image></a>'
            type_name = issue.raw['fields']['issuetype']['name']
            type_url = issue.raw['fields']['issuetype']['iconUrl'] #.replace("&", "&amp;")
            a = ET.Element('a', attrib={'href': 'https://jira.kitenet.com/browse/' + issue.key})
            img = ET.SubElement(a, 'ac:image', { 'ac:class': 'icon', 'ac:alt': type_name})
            ET.SubElement(img, 'ri:url', { 'ri:value': type_url})
            element.append(a)
        elif field == 'key':
            # Key:
            # <a href="https://jira.kitenet.com/browse/' + issue.key + '">' + issue.key + '</a>
            a = ET.Element('a', attrib={'href': 'https://jira.kitenet.com/browse/' + issue.key})
            a.text = issue.key
            element.append(a)
        elif field == 'summary':
            # Summary:
            # <a href="https://jira.kitenet.com/browse/' + issue.key + '">' + summary + '</a>
            a = ET.Element('a', attrib={'href': 'https://jira.kitenet.com/browse/' + issue.key})
            a.text = issue.fields.summary
            element.append(a)
        elif field == 'status':
            # Status:
            # <span class="aui-lozenge aui-lozenge-subtle '+lozenge_class+'">'+status+'</span>
            # Issue status: (funny thing here as using issue... doesn't work even if the fields are actually there...)
            if issue.raw['fields']['status']['statusCategory']['name'] == 'Done':
                lozenge_class = "aui-lozenge-success"
            elif issue.raw['fields']['status']['statusCategory']['name'] == "To Do":
                lozenge_class = "aui-lozenge-current"
            else:
                lozenge_class = "aui-lozenge-complete"
            status = issue.raw['fields']['status']['name'].upper()

            span = ET.Element('span', attrib={'class':'aui-lozenge aui-lozenge-subtle '+lozenge_class})
            span.text = status
            element.append(span)
        elif field == 'resolution':
            # Resolution:
            #  string representing the name of the resolution
            if issue.raw['fields']['resolution']:
                resolution_name =  issue.raw['fields']['resolution']['name']
            else:
                resolution_name = "unresolved"
            element.text = resolution_name
        ## TODO Improvement:
        ##   The custom fields should ideally be handled as an add-on users of the package can register, and can be
        ##   called from here.
        elif field == 'customfield_11402':
            # Issue reviews:
            #  string representing the name of the reviews field (custom field, not generic!)
            if issue.fields.customfield_11402:
                element.text = issue.fields.customfield_11402[0].value
                for review in issue.fields.customfield_11402[1:]:
                    br = ET.SubElement(element, 'br')
                    br.tail = review.value
        elif field == 'customfield_11400':
            # Issue reviewers:
            #  string representing the names of the reviewers field (custom field, not generic!)
            reviewers = ""
            if issue.fields.customfield_11400:
                element.text = issue.fields.customfield_11400[0].displayName + " (" + \
                               issue.fields.customfield_11400[0].name + ")"
                for reviewer in issue.fields.customfield_11400[1:]:
                    br = ET.SubElement(element, 'br')
                    br.tail = reviewer.displayName + " (" + reviewer.name + ")"
        else:
            print("Field '%s' specified for which I don't know how to handle it, dumping a default look and hope for the best" % field)
            element.text = "Unknown field type"

    def create_jira_issue_table(self, issues, fields, titles):
        """ This function takes a list of fields and a list of JIRA issues, and returns a table in
            Confluence formatted code, ready for inclusion on a page.

            Arguments:
                issues: JIRA module return data from 'search_issues' function
                *kwargs: A list of field/title mapping or the mapping as separate dictionaries.
                fields: string of comma separated fields
                titles: string of comma separated titles
        """
        field_list = fields.split(',')
        title_list = titles.split(',')
        if len(field_list) != len(title_list):
            print("Field and title lists are not of equal length")
            exit(1)

        table = ET.Element('table')
        colgroup = ET.SubElement(table, 'colgroup')
        tbody = ET.SubElement(table, 'tbody')
        tr = ET.SubElement(tbody, 'tr')

        for title in title_list:
            ET.SubElement(colgroup, 'col')
            th = ET.SubElement(tr, 'th', attrib={'style':'text-align: left;'})
            span = ET.SubElement(th, 'span', attrib={'class': 'jim-table-header-content'})
            span.text = title

        for issue in issues:
            tr = ET.SubElement(tbody,'tr')
            for field in field_list:
                # Side effect function
                self._field_handler(ET.SubElement(tr, 'td'), field, issue)
        return ET.tostring(table)
    
    def create_table_from_nested_list(self, nestedList):
        """ This function takes a nested list and returns a table in
            Confluence formatted code, ready for inclusion on a page.
            The header column and row is highlighted(gray background). 

            Arguments:
                nestedList: a two dimensional nested list.
        """
        
        table = ET.Element('table')
        colgroup = ET.SubElement(table, 'colgroup')
        tbody = ET.SubElement(table, 'tbody')
        tr = ET.SubElement(tbody, 'tr')

        for release in range(0, len(nestedList[0])):
            ET.SubElement(colgroup, 'col')
            th = ET.SubElement(tr, 'th', attrib={'style':'text-align: left;'})
            span = ET.SubElement(th, 'span', attrib={'class': 'jim-table-header-content'})
            span.text = nestedList[0][release]
        for sprints in range(len(nestedList)-1, 0, -1):
            tr = ET.SubElement(tbody,'tr')
            for release in range(0, len(nestedList[0])):
                if release == 0:
                    ET.SubElement(tr, 'th').text = str(nestedList[sprints][release])
                else:
                    ET.SubElement(tr, 'td').text = str(nestedList[sprints][release])
        return ET.tostring(table)
    
    def create_js_table_from_nested_list(self, nestedList):
        """ This function takes a nested list and returns a table in
            Javascript formated code, ready for inclusion on a page in a html element with js script section..

            Arguments:
                nestedList: a two dimensional nested list.
        """

        table = ",".join(map(str, nestedList))
        table = re.sub("True", "true", table, flags=re.DOTALL)
        table = re.sub("False", "false", table, flags=re.DOTALL)
        table = re.sub("'N_a_N'", "NaN", table, flags=re.DOTALL)
        return table
    
    def create_link_to_teamcity(self, template_page, targetUrl):
        teamcityUrl = "http://kbn-tc-teamcity/viewType.html?buildTypeId=AGILE_HipAesRemainingEstimate41";
    
        template_page = template_page + '\n <ac:structured-macro ac:macro-id="c2a0a348-59c3-4f95-902e-3fa525e68f15" ac:name="info" ac:schema-version="1">\n <ac:parameter ac:name="title">Force update</ac:parameter>\n <ac:rich-text-body>\n <p>If you have changed the mapping of hip items you can force an update of the figure by pressing <strong>run</strong> in this <a href="'+targetUrl+'">link</a>. Do note that it will take minutes before the pages gets updated.</p>\n </ac:rich-text-body> \n </ac:structured-macro>';
    
        return template_page
