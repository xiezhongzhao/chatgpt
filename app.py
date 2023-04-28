#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：chatgpt 
@File    ：app.py
@Author  ：Xie Zhongzhao
@Date    ：2023/4/20 20:59 
'''
import openai
import os
import json
import requests
from flask import Flask, jsonify, request, render_template, redirect, Response
from flask import session

import threading
import asyncio

import userconfig
openai.api_key = "sk-8uv2FNZpydi98uNFOaPGT3BlbkFJfP1aT2knhk1xLwmUK9R"

app = Flask(__name__)
app.config['SECRET_KEY']  = os.urandom(24)
streamFlag = True #默认流式输出

@app.route("/")
def index():
    if "username" not in session:
        return redirect("/login")
    return render_template("chatgpt-clone.html")

@app.route("/show_quotas", methods=["GET"])
def show_quotas():
    if "username" not in session:
        return redirect("/login")
    username = session["username"]
    return userconfig.get_quotas(username)

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

def get_response_stream_generate_from_ChatGPT_API(message_context):

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": message_context}
            ],
            stream=True
        )
        print("response: {}".format(response))
        def generate():
            i = 0
            for chunk in response:
                if chunk["choices"][0]["finish_reason"] is not None:
                    pass
                else:
                    data = chunk["choices"][0]["delta"].get("content", "")
                yield data
                # yield 'data: %s\n\n' % data.replace("\n", "<br/>")
    except Exception as e:
        ee = e
        def generate():
            yield "request error:\n" + str(ee)
    return generate

def handle_message_get_response_stream(message):
    generate = get_response_stream_generate_from_ChatGPT_API(message)
    return generate

@app.route("/returnMessage", methods=["GET", "POST"])
def chatgpt_clone():
    if "username" not in session:
        return redirect("/login")
    username = session["username"]
    question = request.values.get("question").strip()
    print("question: {}".format(question))

    userconfig.check_quota(username)
    if not streamFlag:
        content = get_response_from_ChatGPT_API(question)
        return content
    else:
        generate = handle_message_get_response_stream(question)
        return app.response_class(generate(), mimetype='application/json')

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if userconfig.check_user(username, password):
            session["username"] = username
            return redirect("/")
        else:
            message = "用户名或者密码错误"
    return render_template("login.html", message=message)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route('/newChat', methods=['GET'])
def new_chat():
    """
    新建聊天对象
    :return:
    """
    name = request.args.get("name")
    time = request.args.get("time")
    new_chat_id = 1
    print("新建聊天对象")
    return {"code": 200, "data": {"name": name, "id": new_chat_id, "selected": True}}

if __name__ == '__main__':

    app.run(host="0.0.0.0", port=12346, debug=True)





