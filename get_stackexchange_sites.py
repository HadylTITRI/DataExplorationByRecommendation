import requests

def get_stackexchange_sites():
    url = 'https://api.stackexchange.com/2.2/sites?pagesize=1000'
    response = requests.get(url)
    sites = response.json()['items']
    site_names = [site['name'] for site in sites]
    return site_names

# Sauvegardez les sites dans une liste pour usage ultérieur
stackexchange_sites = get_stackexchange_sites()
