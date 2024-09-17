import requests  # see https://2.python-requests.org/en/master/
import zhmiscellany

connection_data = zhmiscellany.fileio.read_json_file('connection_data.json')

key = connection_data['pastebin']['api_dev_key']
text = "a text"
t_title = "a_paste_title"

login_data = {
    'api_dev_key': key,
    'api_user_name': connection_data['pastebin']['username'],
    'api_user_password': connection_data['pastebin']['password']
}
data = {
    'api_option': 'paste',
    'api_dev_key': key,
    'api_paste_code': text,
    'api_paste_name': t_title,
    'api_user_key': None,
}

login = requests.post("https://pastebin.com/api/api_login.php", data=login_data)
print("Login status: ", login.status_code if login.status_code != 200 else "OK/200")
print("User token: ", login.text)
data['api_user_key'] = login.text

r = requests.post("https://pastebin.com/api/api_post.php", data=data)
print("Paste send: ", r.status_code if r.status_code != 200 else "OK/200")
print("Paste URL: ", r.text)
