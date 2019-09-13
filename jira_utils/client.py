import oauth2 as oauth
import json
import jira.client
import urllib3

##################################################################################
# Python Interface for Confluence, supporting a subset of the full REST interface.
#
# Written for the purpose of allowing commandline updates to Confluence pages.
# This module tries to be as clean as possible and only provide REST functions.
##################################################################################

class Client:
    def __init__(self, oauth=None, jsonOAuthFile=None, options=None, jsonOptionsFile=None):
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
            options = dictionary containing options as follows:
                    server (URL to Confluence server)
                    verify (verify the SSL certificate? currently on https we use false, since we only have a self signed certificate.)
                    

        This is along the lines of how the JIRA module does this.
        """
        if oauth == None:
            # check if the input is specified using json:
            if jsonOAuthFile == None:
                print("No authentication information supplied.")
                exit(1)
            else:
                fp = open(jsonOAuthFile, "r")
                oauthData = json.load(fp)
                oauth = oauthData['oauth'];
                with open(oauthData['keyCertFile'], "r") as key_cert_file:
                    oauth['key_cert'] = key_cert_file.read()
                 

        if options == None:
            # check if the input is specified using json:
            if jsonOptionsFile == None:
                print("No options information supplied.")
                exit(1)
            else:
                fp = open(jsonOptionsFile, "r")
                optionsData = json.load(fp)
                options = optionsData['options']
                if 'timeout' in optionsData:
                    timeout = optionsData['timeout']
                else:
                    timeout = None;

        else:
            if 'timeout' in options:
                timeout = options['timeout']
            else:
                timeout = None

        self._wrapped_obj = obj = jira.client.JIRA(oauth=oauth, options=options, timeout=timeout)

    def __getattr__(self, attr):
        # see if this object has attr
        # NOTE do not use hasattr, it goes into
        # infinite recurrsion
        if attr in self.__dict__:
            # this object has it
            return getattr(self, attr)
        # proxy to the wrapped object
        return getattr(self._wrapped_obj, attr)

