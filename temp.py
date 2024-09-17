import zhmiscellany

connection_data = zhmiscellany.fileio.read_json_file('connection_data.json')

pastebin = zhmiscellany.pastebin.PasteBin(connection_data["pastebin"]["api_dev_key"], connection_data["pastebin"]["api_user_key"])

key = pastebin.paste(data='test')

print(key)

