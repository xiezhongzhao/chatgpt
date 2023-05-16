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

def check_register_user(username):
    with lock:
        with open("userconfig.json", encoding="utf-8") as f:
            datajson = json.loads(f.read())
        print("datajson: {}".format(datajson))
        print("username: {}".format(username))
        if username in datajson:
            return True
        return False

def check_register_passwd(passwd, passwd_again):
    with lock:
        if passwd == passwd_again:
            return True
        else:
            return False

def write_register_user_passwd(username, passwd):
    with lock:
        new_user_passwd = {
            username: {
                "password": passwd,
                "quota": 100,
                "visited": 0,
                "remark": "note"
            }
        }
        with open("userconfig.json", "r", encoding="utf-8") as f:
            datajson = json.load(f)
            datajson.update(new_user_passwd)

        with open("userconfig.json", "w", encoding="utf-8") as f:
            json.dump(datajson, f, ensure_ascii=False, indent=4)

def write_forget_passwd(username, newPasswd):
    with lock:
        with open("userconfig.json", "r", encoding="utf-8") as f:
            load_dict = json.load(f)
            load_dict[username]["password"] = newPasswd
            with open("userconfig.json", "w", encoding="utf-8") as f:
                json.dump(load_dict, f, ensure_ascii=False, indent=4)

def check_captcha(random_code, input_captcha):
    with lock:
        if random_code.upper() == input_captcha.upper():
            return True
        else:
            return False

def check_quota(username):
    with lock:
        with open("userconfig.json", encoding="utf-8") as f:
            datajson = json.loads(f.read())
        if username in datajson:
            visited = datajson[username]["visited"]
            quota = datajson[username]["quota"]
            if visited > quota:
                return "over the quota"
                # raise Exception("{}/{}".format(visited, quota))
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
        print("username in json: ", username)
        return ""






