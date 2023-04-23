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
from flask import Flask, jsonify, request, render_template, redirect, Response
from flask import session

import userconfig

openai.api_key = "your openai key"

app = Flask("chatgpt")
app.secret_key = "adfgjsljglsdjgdsjgjdsgfjdsolgfji"

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

@app.route("/chatgpt-clone", methods=["POST", "GET"])
def chatgpt_clone():
    if "username" not in session:
        return redirect("/login")
    username = session["username"]
    question = request.args.get("question", "")
    # question = request.form.get("question", "")
    question = str(question).strip()
    if question:
        def stream():
            try:
                userconfig.check_quota(username)
            except Exception as e:
                yield "data: %s\n\n"%str(e)
                yield "data: [DONE]\n\n"
                return
            result = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": question}
                ],
                stream=True
            )
            for chunk in result:
                if chunk["choices"][0]["finish_reason"] is not None:
                    data = "[DONE]"
                else:
                    data = chunk["choices"][0]["delta"].get("content", "")
                yield 'data: %s\n\n'%data.replace("\n", "<br/>")

        # content = result["choices"][0]["message"]["content"]
        # return content.replace("\n", "<br />")
        return Response(stream(), mimetype="text/event-stream")
    return "no content"

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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=12346)





