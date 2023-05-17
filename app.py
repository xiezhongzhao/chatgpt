#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：chatgpt 
@File    ：app.py
@Author  ：Xie Zhongzhao
@Date    ：2023/4/20 20:59 
'''
import random
import uuid

import openai
import os
import json
import requests
from flask import Flask, jsonify, request, render_template, redirect, Response
from flask import session, make_response

import threading
import asyncio
import pickle
from io import BytesIO
import base64

import userconfig
from verification import check_code
from mail import emailSendInfo

openai.api_key = "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"

app = Flask(__name__)
app.config['SECRET_KEY']  = os.urandom(24)
streamFlag = True #默认流式输出
user_dict_file = "all_user_dict.pkl" # 用户信息存储文件
CHAT_CONTEXT_NUMBER_MAX = 5
lock = threading.Lock() # 用于线程锁

def init_user_info(username):
    lock.acquire()
    datajson = dict()
    datajson["chats"] = {"0": {"name": "默认对话",
                               "chat_with_history": True,
                               "have_chat_context": 0,
                               "messages_history": [{"role": "assistant", "content": "您想聊什么？"}]}}
    datajson["selected_chat_id"] = str(0)
    datajson["default_chat_id"] = str(0)
    with open(username+".json", "w", encoding="utf-8") as f:
        json.dump(datajson, f, ensure_ascii=False, indent=4)
    lock.release()


def get_user_info(username):
    global user_info #设置为全局变量
    lock.acquire()
    with open(username+".json", "r", encoding="utf-8") as f:
        user_info = json.load(f)
    lock.release()
    return user_info

async def save_user_info():
    '''
    异步存储user_info
    :return:
    '''
    await asyncio.sleep(0)
    lock.acquire()
    username = session.get("username")
    with open(username+".json", "w", encoding="utf-8") as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4)
    lock.release()

def get_response_from_ChatGPT_API(message_context):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": message_context}
            ],
            stream=False
        )
        print("response: {}".format(response))
        # 判断是否含有choices[0].message.content
        if "choices" in response \
                and len(response["choices"]) > 0 \
                and "message" in response["choices"][0] \
                and "content" in response["choices"][0]["message"]:
            data = response["choices"][0]["message"]["content"]
        else:
            data = str(response)

    except Exception as e:
        print(e)
        return str(e)
    return data

def get_response_stream_generate_from_ChatGPT_API(message_context, messages_history):
    """
    输入上下文消息给openai接口
    :param message_context:
    :param message_history:
    :return:
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = message_context,
            # messages=[
            #     {"role": "user", "content": message_context}
            # ],
            stream=True
        )
        print("response: {}".format(response))
        def generate():
            stream_content = str()
            one_message = {"role": "assistant", "content": stream_content}
            messages_history.append(one_message)
            i = 0
            for chunk in response:
                if chunk["choices"][0]["finish_reason"] is not None:
                    pass
                else:
                    data = chunk["choices"][0]["delta"].get("content", "")
                    one_message["content"] = one_message["content"] + data
                yield data
                # yield 'data: %s\n\n' % data.replace("\n", "<br/>")
    except Exception as e:
        ee = e
        def generate():
            yield "request error:\n" + str(ee)
    return generate

def get_message_context(message_history, have_chat_context, chat_with_history):
    '''
    获取上下文
    :param message_history:
    :param have_chat_context:
    :param chat_with_history:
    :return:
    '''
    message_context = []
    total = 0
    if chat_with_history:
        num = min([len(message_history), CHAT_CONTEXT_NUMBER_MAX, have_chat_context])
        # 获取所有有效聊天记录
        valid_start = 0
        valid_num = 0
        for i in range(len(message_history) - 1, -1, -1): # 逆序遍历
            message = message_history[i]
            if message['role'] in {'assistant', 'user'}:
                valid_start = i
                valid_num += 1
            if valid_num >= num:
                break

        for i in range(valid_start, len(message_history)):
            message = message_history[i]
            if message['role'] in {'assistant', 'user'}:
                message_context.append(message)
                total += len(message['content'])
    else:
        message_context.append(message_history[-1])
        total += len(message_history[-1]['content'])

    print(f"len(message_context): {len(message_context)} total: {total}", )
    return message_context

def handle_message_get_response_stream(message, messages_history, have_chat_context, chat_with_history):
    messages_history.append({"role": "user", "content": message})
    message_context = get_message_context(messages_history, have_chat_context, chat_with_history)
    ### 输入上下文信息给openai推理
    print("message_context: ", message_context)
    generate = get_response_stream_generate_from_ChatGPT_API(message_context, messages_history)
    asyncio.run(save_user_info())
    return generate

@app.route('/saveChat', methods=["GET", "POST"])
def saveChat():
    asyncio.run(save_user_info())
    return {"data": "success"}

@app.route('/getMode', methods=["GET"])
def get_mode():
    """
    获得当前对话方式
    :return:
    """
    user_info = get_user_info(session.get('username'))
    chat_id = user_info["selected_chat_id"]
    chat_with_history = user_info["chats"][chat_id]["chat_with_history"]
    if chat_with_history:
        return {"mode": "continuous"}
    else:
        return {"mode": "normal"}

@app.route('/changeMode/<status>', methods=["GET"])
def change_mode(status):
    """
    切换对话模式
    :param status:
    :return:
    """
    user_info = get_user_info(session.get('username'))
    chat_id = user_info["selected_chat_id"]
    if status == "normal":
        user_info["chats"][chat_id]["chat_with_history"] = False
        print("开启普通对话")
        message = {"role": "system", "content": "切换为普通对话"}
    else:
        user_info["chats"][chat_id]["chat_with_history"] = True
        user_info["chats"][chat_id]["have_chat_context"] = 0
        print("开启连续对话")
        message = {"role": "system", "content": "切换为连续对话"}
    user_info["chats"][chat_id]["messages_history"].append(message)
    asyncio.run(save_user_info())
    return {"code": 200, "data": message}

@app.route('/loadHistory', methods=["GET", "POST"])
def load_messages():
    '''
    加载聊天记录
    :return:
    '''
    user_info = get_user_info(session.get('username'))
    chat_id = user_info["selected_chat_id"]
    print("chat_id: ", chat_id)
    messages_history = user_info["chats"][chat_id]["messages_history"]
    print(f"用户({session.get('username')})加载聊天记录，共{len(messages_history)}条记录")
    return {"code": 0, "data": messages_history, "message": ""}

@app.route('/deleteHistory', methods=['GET'])
def delete_history():
    '''
    清空当前聊天记录
    :return:
    '''
    user_info = get_user_info(session.get('username'))
    chat_id = user_info["selected_chat_id"]
    default_chat_id = user_info['default_chat_id']
    if default_chat_id == chat_id:
        print("清空历史记录")
        user_info["chats"][chat_id]["messages_history"] = user_info["chats"][chat_id]["messages_history"][:1]
    else:
        print("删除聊天对话")
        user_info["chats"].pop(chat_id)
        # del user_info["chats"][chat_id]
    user_info["selected_chat_id"] = default_chat_id
    asyncio.run(save_user_info())
    return "delete"


@app.route('/loadChats', methods=["GET", "POST"])
def load_chats():
    '''
    加载聊天联系人
    :return: 聊天联系人
    '''
    user_info = get_user_info(session.get('username'))
    chats = []
    for chat_id, chat_info in user_info['chats'].items():
        chats.append(
            {"id": chat_id,
             "name": chat_info["name"],
             "selected": chat_id == user_info['selected_chat_id']}
        )
    print(chats)
    return {"code": 0, "data": chats, "message": ""}

@app.route('/selectChat', methods=['GET'])
def select_chat():
    """
    选择聊天对象
    :return:
    """
    chat_id = request.args.get("id")
    chat_id = chat_id.split("data-name")[0]

    user_info["selected_chat_id"] = chat_id
    asyncio.run(save_user_info())
    return {"code": 200, "msg": "选择聊天对象成功"}

@app.route('/newChat', methods=['GET'])
def new_chat():
    """
    新建聊天对象
    :return:
    """
    name = request.args.get("name")
    time = request.args.get("time")

    username = session.get("username")
    user_info = get_user_info(username)

    new_chat_id = str(uuid.uuid1())
    user_info["selected_chat_id"] = new_chat_id
    user_info["chats"][new_chat_id] = \
                                    {"name": name,
                                     "chat_with_history": True,
                                     "have_chat_context": 0,
                                     "messages_history": []}

    asyncio.run(save_user_info())
    print("新建聊天对象")
    return {"code": 200, "data": {"name": name, "id": new_chat_id, "selected": True}}


@app.route("/")
def index():
    if "username" not in session:
        return redirect("/login")
    return render_template("chatgpt-clone.html")

@app.route("/show_quotas", methods=["GET"])
def show_quotas():
    global username
    if "username" not in session:
        return redirect("/login")
    username = session["username"]
    return userconfig.get_quotas(username)

@app.route("/returnMessage", methods=["GET", "POST"])
def chatgpt_clone():
    if "username" not in session:
        return redirect("/login")
    username = session["username"]
    question = request.values.get("question").strip()
    send_time = request.values.get("send_time").strip()
    print("question: {}".format(question))
    print("send_time: {}".format(send_time))

    user_info = get_user_info(session.get("username"))
    chat_id = user_info["selected_chat_id"]
    messages_history = user_info["chats"][chat_id]["messages_history"]
    chat_with_history = user_info["chats"][chat_id]["chat_with_history"]
    have_chat_context = user_info['chats'][chat_id]['have_chat_context']
    if chat_with_history:
        user_info["chats"][chat_id]["have_chat_context"] += 1
    if userconfig.check_quota(username) == "over the quota":
        return "余额为0，请充值后继续使用"
    if not streamFlag:
        content = get_response_from_ChatGPT_API(question)
        return content
    else: ### 处理聊天数据
        username = session.get("username")
        print("用户{}发送消息:{}".format(username, question))
        generate = handle_message_get_response_stream(question,
                                                      messages_history,
                                                      have_chat_context,
                                                      chat_with_history)
        if chat_with_history:
            user_info["chats"][chat_id]["have_chat_context"] += 1
        return app.response_class(generate(), mimetype='application/json')


@app.route("/captcha")
def captcha():
    img, code_string = check_code()
    # 图片以二进制方式写入
    buf = BytesIO()
    img.save(buf, 'jpeg')
    buf_str = buf.getvalue()
    # 把buf_str作为response返回前端，并设置首部字段
    response = make_response(buf_str)
    response.headers['Content-Type'] = 'image/gif'
    session['captcha'] = code_string
    return response

@app.route("/sendMail", methods=["GET", "POST"])
def sendMail():
    if request.method == "POST":
        username = request.form.get("username")
    if request.method == "GET":
        username = request.args.get("username")

    if len(username) == 0:
        return {'message': "请输入邮件地址"}
    # print("username: ", username)
    # print("type(username): ", type(username))

    random_email_code = random.randint(10000, 99999)
    session['code'] = str(random_email_code)
    # print("send code: ", random_email_code)
    # print("type(send_code): ", type(random_email_code))
    content = "您的验证码是: {}, 请勿告诉其他人".format(random_email_code)
    emailSendInfo("重置密码", content, username)
    return {'message': "邮件已发送"}

@app.route("/forgetPasswd", methods=["GET", "POST"])
def forgetPasswd():
    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        email_code =  request.form.get("email_code")
        password = request.form.get("password")
        password_again = request.form.get("password_again")

        print(session.keys())
        if 'code' not in session.keys():
            session['code'] = 0
        random_email_code = session['code']

        # print("user email: ", email_code)
        # print("random_email_code: ", random_email_code)

        if not userconfig.check_register_user(username): ### 检测该用户是否在数据库中
            message = "用户不存在, 请注册"
            return render_template("forgetPasswd.html", message=message)

        if not userconfig.check_register_passwd(password, password_again):
            message = "两次输入密码不一致"
            return render_template("forgetPasswd.html", message=message)
        if len(email_code) != 5 or email_code != random_email_code:
            message = "验证码错误"
            return render_template("forgetPasswd.html", message=message)

        if email_code == random_email_code:
            ### 写入新的密码到数据库当中
            message = "密码修改成功"
            userconfig.write_forget_passwd(username, password)
            return render_template("forgetPasswd.html", message=message)

    return render_template("forgetPasswd.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_again = request.form.get("password_again")

        print("flag: ", userconfig.check_register_user(username))
        if userconfig.check_register_user(username):
            message = "用户已经存在, 请直接登录"
            print("message: ", message)
            return render_template("register.html", message=message)

        if userconfig.check_register_passwd(password, password_again):
            # 将注册的用户名和密码写入数据库
            userconfig.write_register_user_passwd(username, password)
            return redirect("/login")
        else:
            message = "两次密码不一致"
    return render_template("register.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    global username
    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        input_captcha = request.form.get("code")
        random_code = session['captcha']

        # print("random_code: ", random_code)
        # print("input_captcha: ", input_captcha)
        if userconfig.check_user(username, password) \
                and userconfig.check_captcha(random_code, input_captcha):
            session["username"] = username
            if os.path.exists(username+".json"):
                return redirect("/")
            else:
                init_user_info(username)
            return redirect("/")
        elif not userconfig.check_captcha(random_code, input_captcha):
            message = "验证码错误"
        elif not userconfig.check_user(username, password):
            message = "用户名或密码错误"
    return render_template("login.html", message=message)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=12346, debug=True)





