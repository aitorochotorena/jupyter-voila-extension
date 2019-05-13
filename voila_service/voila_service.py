import requests
import os
import sys
from urllib.parse import urlparse
import time

PROXY_TOKEN = os.environ['PROXY_TOKEN']
PROXY_API_URL = os.environ['PROXY_API_URL']
MAX_RETRIES = os.environ.get("MAX_RETRIES", 10)
VOILA_PORT = os.environ.get("VOILA_PORT", 8866)
SYNC_TIMEOUT = os.environ.get('SYNC_TIMEOUT', 5)

def run():
  retries = 0
  time.sleep(5)
  while True:
    res = requests.get(os.path.join(PROXY_API_URL, "api/routes"), headers={'Authorization': 'token %s' % PROXY_TOKEN})
    if res.status_code != 200:
      retries += 1
      if retries >= MAX_RETRIES:
        sys.exit(1)

    data = res.json()
    users = []
    for key, val in data.items():
        if key.startswith("/user") and not key.endswith("voila"):
          voila_route = data.get(os.path.join(key, "voila"))
          if voila_route:
            voila_hostname = urlparse(voila_route['target'])
            current_hostname = urlparse(val['target'])
            if voila_hostname.hostname != current_hostname.hostname:
              users.append((key, "update"))
          else:
            users.append((key, "add"))
        else:
          try:
            if users[users.remove(key[:-7])][1] != "update":
              users.remove(key[:-7])
          except ValueError as e:
            #Delete public route for non-existent user!
            pass

    if len(users) > 0:
      for user in users:
        target = urlparse(data[user[0]]["target"])
        print(target)
        new_target_url = "%s://%s:%s" % (target.scheme, target.hostname, str(VOILA_PORT))
        print(os.path.join(PROXY_API_URL, "api/routes", user[0], "voila"))
        res_post = requests.post(os.path.join(PROXY_API_URL, "api/routes", user[0].strip("/"), "voila"), json={"target": new_target_url}, headers={'Authorization': 'token %s' % PROXY_TOKEN})
        if res_post.status_code != 201:
          print("Failed to create route for %s" % user)

    time.sleep(SYNC_TIMEOUT)
