import zhmiscellany

connection_data = zhmiscellany.fileio.read_json_file('connection_data.json')

#pastebin = zhmiscellany.pastebin.PasteBin(connection_data['pastebin']['api_dev_key'], connection_data['pastebin']['api_user_key'])

seed = zhmiscellany.string.get_universally_unique_string()

#print(f'{seed}.'*10)

#for i in range(100):
#    seed = zhmiscellany.string.get_universally_unique_string()
#    r = pastebin.paste(f'{seed}.'*10, guest=True, expire='10M', name=seed, private=0)
#    print(r)
pastebin = zhmiscellany.pastebin.Pasteee(connection_data['pasteee']['app_key'])

#r = pastebin.paste(data='test', name=f'hi', expire=60*10)
#print(r)
#r = pastebin.paste(data=f'{seed}.'*10, name=f'{seed}_offer_{seed}')
r = pastebin.raw_pastes('2lzvw')
#r = pastebin.list_pastes(1000)
print(r)

#print(pastebin.list_pastes(1000))