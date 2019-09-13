import base64
import oauth2 as oauth
from tlslite.utils import keyfactory
import json

##################################################################################
# Python Interface for Confluence, supporting a subset of the full REST interface.
#
# Written for the purpose of allowing commandline updates to Confluence pages.
# This module tries to be as clean as possible and only provide REST functions.
##################################################################################


class SignatureMethod_RSA_SHA1(oauth.SignatureMethod):
    name = 'RSA-SHA1'
    private_key = None

    def signing_base(self, request, consumer, token):
        if not hasattr(request, 'normalized_url') or request.normalized_url is None:
            raise ValueError("Base URL for request is not set.")

        sig = (
            oauth.escape(request.method),
            oauth.escape(request.normalized_url),
            oauth.escape(request.get_normalized_parameters()),
        )

        key = '%s&' % oauth.escape(consumer.secret)
        if token:
            key += oauth.escape(token.secret)
        raw = '&'.join(sig)
        return key, raw

    def sign(self, request, consumer, token):
        """Builds the base signature string."""
        key, raw = self.signing_base(request, consumer, token)
        parsed_key = keyfactory.parsePrivateKey(self.private_key)
        signature = parsed_key.hashAndSign(bytes(raw, "utf-8"))

        return base64.b64encode(signature)


class Client:
    _headers = {'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Atlassian-Token': 'no-check'}

    def __init__(self, oauth=None, jsonFile=None, options=None):
        """ Arguments:
            oauth = dictionary containing the following fields
                    access_token
                    access_token_secret
                    consumer_key
                    consumer_secret (optional)
                    key_cert
            jsonFile = A json file specifying the oauth details. containing the following fields:
                    "oauth":{
                        "access_token"        : "*",
                        "access_token_secret" : "*",
                        "consumer_key"        : "*",
                        "consumer_secret"     : "*"},
                    "keyCertFile"             : "./*.pem"
}
            options = dictionary containing options as follows
                    server (URL to Confluence server)
                    spacekey (name of the Space to manipulate)

        This is along the lines of how the JIRA module does this.
        """
        if oauth != None and jsonFile != None:
            print("Only one source of authentication information can be supplied. Either oauth or jsonFile")
            exit(1)
        
        if oauth == None:
            # check if the input is specified using json:
            if jsonFile == None:
                print("No authentication information supplied.")
                exit(1)
            else:
                fp = open(jsonFile, "r")
                oauthData = json.load(fp)
                oauth = oauthData['oauth'];
                with open(oauthData['keyCertFile'], "r") as key_cert_file:
                    oauth['key_cert'] = key_cert_file.read()
                 

        if options is None or not 'server' in options or not 'spacekey' in options:
            print("None or missing options supplied. Declare 'server' URL and 'spacekey'.")
            exit(1)

        self._auth = oauth
        self._server_url = options['server']+"/rest/api/"
        self._spacekey = options['spacekey']

        # Prepare the initial client
        self._set_client()

    def _set_client(self):
        # Setup a new client. We need to repeat the authentication for every POST request due to nonce handling.
        consumer = oauth.Consumer(self._auth['consumer_key'], self._auth['consumer_secret'])
        access_token = oauth.Token(self._auth['access_token'], self._auth['access_token_secret'])
        self._client = oauth.Client(consumer, access_token)
        SignatureMethod_RSA_SHA1.private_key = self._auth['key_cert']
        self._client.set_signature_method(SignatureMethod_RSA_SHA1())

    ## VERSION
    ##########
    def get_next_page_version(self, page_id):
        # return string of the next version number of this page.
        page_id = str(page_id)

        uri = self._server_url+"content/" + page_id + "/history?expand=lastUpdated"
        resp, content = self._client.request(uri, method="GET")
        data = json.loads(content.decode("utf-8"))
        return str(data['lastUpdated']['number'] + 1)

    ## PAGE
    #######
    def update_page(self, page_id, title, body):
        # PUT new content on an existing page
        page_id = str(page_id)

        next_version = self.get_next_page_version(page_id)
        uri = self._server_url+"content/" + page_id
        data = {'type': 'page',
                'title': title,
                'space': {
                    'key': self._spacekey
                },
                'body': {
                    'storage': {
                        'value': body,
                        'representation': 'storage'
                    }
                },
                'version': {
                    'number': next_version
                }}
        data_json = json.dumps(data).encode("utf-8")
        resp, content = self._client.request(uri, headers=self._headers, body=data_json, method="PUT")
        return content

    def create_page(self, parent_page_id, title, body):
        # consider updating or renaming the new page the page if it already exists instead of failing
        # Also ancestor is not strictly required. If ommitted a page with no ancestor is created (an orphan)
        self._set_client()

        parent_page_id = str(parent_page_id)
        uri = self._server_url+"content/"
        data = {"type": "page",
                "ancestors": [
                    {"type": "page",
                     "id": parent_page_id
                     }],
                "title": title,
                "space": {
                    "key": self._spacekey
                },
                "body": {
                    "storage": {
                        "value": body,
                        "representation": "storage"
                    }}
                }
        data_json = json.dumps(data).encode("utf-8")
        # print " JSON data:\n"
        # print data_json+"\n"
        resp, content = self._client.request(uri, headers=self._headers, body=data_json, method="POST")
        # print resp
        # print content
        return content

    def get_page_content(self, page_id):
        page_id = str(page_id)

        uri = self._server_url+"content/" + page_id + "?expand=body.storage"
        resp, content = self._client.request(uri, method="GET")
        data = json.loads(content.decode("utf-8"))

        # print "CONTENT:\n"+content+"\n"
        return data['body']['storage']['value']

    def add_attachment(self, page_id, filename, comment):
        # PUT new content on an existing page
        page_id = str(page_id)

        uri = self._server_url+"content/" + page_id+"/child/attachment"
        data = {'file': "@"+filename}
        
        #curl -v -S -u admin:admin -X POST -H "X-Atlassian-Token: no-check" -F "file=@myfile.txt" -F
#"comment=this is my file" "http://localhost:8080/confluence/rest/api/content/3604482/child/attachment"
#| python -mjson.tool
        data_json = json.dumps(data).encode("utf-8")
        
        resp, content = self._client.request(uri, headers={"X-Atlassian-Token": "no-check"}, body=data_json, method="POST")
        print(content)
        return content

    ## LABELS
    ##########
    def set_labels(self, page_id, labels=None):
        # Set the labels of some content page
        if labels is None:
            return "No labels to add specified"

        self._set_client()

        page_id = str(page_id)
        uri = self._server_url+"content/"+page_id+"/label"

        data = list()
        for label in labels:
            # Labels specified cannot contains spaces, so we convert spaces to underscores first
            label = label.replace(" ", "_")
            data.extend([{"prefix": "global", "name": label}])
        data_json = json.dumps(data).encode("utf-8")

        resp, content = self._client.request(uri, headers=self._headers, body=data_json, method="POST")
        return content

    def delete_label(self, page_id, label=None):
        # Delete a single label of some content page
        if label is None:
            return "No label to delete specified"

        page_id = str(page_id)
        uri = self._server_url+"content/"+page_id+"/label?name="+label

        resp, content = self._client.request(uri, headers=self._headers, method="DELETE")
        return content
    
    def print_status(self, status):
        # This method takes a byte array-representation of a JSON dictionary, as received from the confluence call.
        # The method extracts relevant data and prints the output or throws exception in case the status is an error.

        status = json.loads(status.decode('UTF-8'));
        if "statusCode" in status:
            if 'statusCode' in status and 'message' in status:
                raise RuntimeError("Confluence page was not created!\nStatusCode="+str(status['statusCode']) + ", " + status['message'])
            else:
                raise RuntimeError("Confluence page was not created!")
        else:
            if 'title' in status and 'space' in status and 'key' in status['space']:
                print("Confluence page created successfully with title " + status['title'] + " in space " + status['space']['key'])
            else:
                print("Confluence page created successfully");
                
                

