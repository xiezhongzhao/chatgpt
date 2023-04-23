import threading
import json

lock = threading.Lock()
def check_user(username, password):
    with lock:
        with open("userconfig.json", encoding="utf-8") as f:
            datajson = json.loads(f.read())
        print("username: {}".format(username))
        print(datajson.get(username).get("password"))
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
                raise Exception(f"您配额为{quota}次，已使用{visited}次".format(quota, visited-1))
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
            return "您当前的总配额是{}次，已经使用{}次，还剩{}次".format(quota, visited, max(0, quota-visited))
        return ""
