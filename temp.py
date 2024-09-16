import requests, zhmiscellany
from pastebin import PasteBin

connection_data = zhmiscellany.fileio.read_json_file('connection_data.json')

pastebin = PasteBin(connection_data["pastebin"]["api_key"])

key = pastebin.create_user_key(connection_data["pastebin"]["username"], connection_data["pastebin"]["password"])

print(key)