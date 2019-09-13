import json
import time

config = {
    'template_page_id': 61210645, # The page on which to substitute variables. Get the page id from the confluence viewPage URL
    'parent_page_id': 61210633,   # The page on whic to create a child page.
    'test_mode': 0,
    "spacekey"         : "<SPACE KEY>"
    }
variables = {
    "REVIEW_DATE": time.strftime("%Y-%m-%d"), # percentage sign must be escaped in TC with a percentage sign
    "RELEASE_VERSION": "4.8.0",
  }
allData = {"config" : config,
           "variables" : variables}

#Write dictionary to file in JSON format.
with open('DRscriptInputs.txt', 'w') as scriptInputs:
    json.dump(allData, scriptInputs, sort_keys=True, indent=2)

#Print the contents of the file to console:
print(json.dumps(allData, sort_keys=True, indent=2))
