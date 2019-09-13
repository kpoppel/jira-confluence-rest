import confluence
import datetime

def get_confluence_client():
    """ The minimal setup to get access to Confluence"""
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
        'server': 'http://<SERVER URL>',
        'spacekey': "<SPACE KEY>"
    }

    return confluence.Client(oauth=oauth_data, options=options)

def main():
    # A small test of the confluence package
    cc = get_confluence_client()

    print("\nGet Next Page version:\n-------------")
    page_id = 61210635  # demo page
    next_version = cc.get_next_page_version(page_id)
    print(next_version)

    print("\nUpdate Page:\n-------------")
    page_id = 61210635  # demo page
    body = '<p>This is the updated text for the new page</p><p>This page has version ' + next_version + '</p>'
    print(cc.update_page(page_id=page_id, title='new page', body=body))

    print("\nGet Page:\n-------------")
    page_id = 61210635
    body = cc.get_page_content(page_id)
    print(body)

    # Create a page (with a unique name)
    print("\nCreate Page:\n-------------")
    parent_page_id = 61210633
    body = '<p>Look I can create new pages too!!!</p>'
    content = cc.create_page(parent_page_id=parent_page_id,
                             title=datetime.datetime.now().strftime("%Y-%m-%d %H%M%S")+' new page created',
                             body=body)
    print(content)

    print("\nGenerate Page:\n-------------")
    variables = {'SUBST_1': "Wow I substituted SUBST_1",
                 'SUBST_2': "Wow I substituted SUBST_2"
                 }
    # Use the utilities.
    cu = confluence.ContentUtils(cc)
    content = cu.generate_page_from_template(parent_page_id=61210633,
                                             template_page_id=61210637,
                                             title=datetime.datetime.now().strftime("%Y-%m-%d %H%M%S")+" - Report",
                                             substitutions=variables)
    print(content)

    print("\nSet labels:\n-------------")
    page_id = 61210635
    content = cc.set_labels(page_id, labels=["label_1", "my fancy label"])
    print(content)

    print("\nDelete labels:\n-------------")
    page_id = 61210635
    content = cc.delete_label(page_id, label="label_1")
    print(content)

# Run the whole test
main()