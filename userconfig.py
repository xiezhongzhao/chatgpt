import threading
import json

lock = threading.Lock()
def check_user(username, password):
    with lock:
        with open("userconfig.json", encoding="utf-8") as f:
            datajson = json.loads(f.read())
        print("username: {}".format(username))
        # print(datajson.get(username).get("password"))
        if username in datajson:
            if password == datajson.get(username).get("password"):
                return True
        return False


def check_quota(username):
    with lock:
        with open("userconfig.json", encoding="utf-8") as f:
            datajson = json.loads(f.read())
        if username in datajson:
            visited = datajson[username]["visited"]
            quota = datajson[username]["quota"]
            if visited > quota:
                raise Exception("{}/{}".format(visited, quota))
            datajson[username]["visited"] += 1
            with open("userconfig.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(datajson, ensure_ascii=False, indent=4))
        return False

def get_quotas(username):
    with lock:
        with open("userconfig.json", encoding="utf-8") as f:
            datajson = json.loads(f.read())
        if username in datajson:
            visited = datajson[username]["visited"]
            quota = datajson[username]["quota"]
            return "{}/{}".format(visited, quota)
        return ""
