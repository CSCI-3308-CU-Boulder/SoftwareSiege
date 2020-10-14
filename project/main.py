#!/usr/bin/env python3
import time

from bottle import route, run, request, response, post, redirect, static_file
from mako.template import Template
import pykka
from typeguard import typechecked
from passlib.hash import argon2
import sqlite3
from typing import List, Union, Callable, Tuple, Dict, Any
import random
from uuid import uuid4
import os

SCHEMA_USER = ["uid", "username", "email", "password"]
SCHEMA_TASK = ["tid", "name", "body", "priority", "due_date", "added_date"]

@typechecked
def DEV_PRINT_HTML_TABLE(a: List[Union[List, Tuple]]) -> str:
    return "<table><tr>"+"</tr><tr>".join(["<td>"+"</td><td>".join(i)+"<td>" for i in [[repr(x) for x in y] for y in a]])+"</tr></table>"

@typechecked
class DatabaseActor(pykka.ThreadingActor):
    def __init__(self, filename):
        super(DatabaseActor, self).__init__()
        self._con = sqlite3.connect(filename, check_same_thread=False, isolation_level=None)

        self._c = self._con.cursor()


    def on_receive(self, message: List[Union[str, List]]) -> Union[List, None]:
        print(message)
        self._c.execute(*message)
        self._con.commit()
        return self._c.fetchall()


    # TODO conn.close()

# Globals
db: DatabaseActor = None
login_tokens: Dict[str, int] = {}

@typechecked
def query(q: str, params: List=None) -> List[Tuple]:
    if params is None:
        params = []
    global db
    return db.ask([q, params])

@typechecked
def db_dictify(data: Tuple, schema) -> Dict[str, Any]:
    d = list(data)
    end = {}
    for i,j in enumerate(schema):
        end[j] = d[i]
    return end


@route('/dev_list_tasks')
def Route_list_tasks():
    return DEV_PRINT_HTML_TABLE(query("select * from tasks"))

@route('/dev_list_users')
def Route_list_users():
    return DEV_PRINT_HTML_TABLE(query("select * from users"))

@route('/dev_login_as/<who>')
def Route_login_as(who: int):
    new_token=str(uuid4())
    response.set_cookie("login_token", new_token, path="/")
    login_tokens[new_token] = who
    return "Now logged in as "+db.ask(["select username from users where uid=?", [who]])[0][0]

@route('/whoami')
def Route_whoami():
    token = request.get_cookie("login_token")
    if token and token in login_tokens.keys():
        who = db_dictify(query("select * from users where uid=?", [login_tokens[token]])[0], SCHEMA_USER)
        return repr(who) # repr looks a lot like json BUT IT ISN'T
    else:
        return "You are not logged in!"

@route('/myprojects')
def Route_myprojects():
    token = request.get_cookie("login_token")
    if token and token in login_tokens.keys():
        projects_raw = query("select uppid from userprojects where upuid=?", [login_tokens[token]])
        projects = []
        for i, in projects_raw:
            name = query("select name from projects where pid=?", params=[i])[0][0]
            projects.append((i, name))
        return Template(open("templates/myprojects.html").read()).render(projects=projects)
    else:
        return "You are not logged in!"

@route('/login')
def Route_login():
    return Template(open("templates/login.html").read()).render(failure=False)

@post('/login')
def Post_login():
    username = request.forms.get('username')
    password = request.forms.get('password')

    q = query("select * from Users where username=?", params=[username])
    if len(q) == 0:
        # prevent timing attacks
        argon2.hash("whatever")
        return Template(open("templates/login.html").read()).render(failure=True)
    else:
        user = db_dictify(q[0], SCHEMA_USER)
        correct = argon2.verify(password, user["password"])
        if correct:
            new_token = str(uuid4())
            response.set_cookie("login_token", new_token, path="/")
            login_tokens[new_token] = user["uid"]
            redirect("/myprojects")
            return
        else:
            return Template(open("templates/login.html").read()).render(failure=True)

@route('/register')
def Route_register():
    return Template(open("templates/register.html").read()).render(failure=False)

@post('/register')
def Post_register():
    username = request.forms.get('username')
    password = request.forms.get('password')
    email = request.forms.get('email')

    q = query("select * from users where username =?", params=[username])
    if len(q):
        return Template(open("templates/register.html").read()).render(failure=f"Username '{username}' already in use!")

    query("insert into users (username, email, password) values (?, ?, ?)", params=[username, email, argon2.hash(password)])
    id = query("select uid from users where username=?", params=[username])[0][0]


    new_token = str(uuid4())
    response.set_cookie("login_token", new_token, path="/")
    login_tokens[new_token] = id

    # TODO TEMPORARY add them to the example project
    query("insert into userprojects values (1, ?)", params=[id])

    redirect("/myprojects")


@route("/logout")
def Route_logout():
    response.delete_cookie("login_token")
    redirect("/whoami")

@route("/project/<id>")
def Route_project(id):
    token = request.get_cookie("login_token")
    # TODO, we have if False to make development easier. We will probably allow the user to add themselves to any project, so checking that they have access is probably not important
    if False and token not in login_tokens.keys():
        redirect("/login")
        return

    q = query("select name from projects where pid=?", params=[id])
    if len(q) == 0:
        return f"No such project {id}"

    tasks = query("select * from tasks where project=?", params=[id])
    return Template(open("templates/project.html").read()).render(tasks=tasks)

@route('/static/<path:path>')
def Route_static_files(path):
    # run the program in this directory or it won't work.
    # if we have to run it with systemd or something, can just write a bash script that does cd $(dirname $0)
    return static_file(path, os.getcwd()+"/static/")

@route("/")
def index_login_redirect():
    redirect("/login")


def main(database_file):
    global db
    db = DatabaseActor.start(database_file)
    run(host='localhost', port=8830)

def fill_tmp_db(add: Callable[[Tuple[str, Union[List, None]]], None]):
    for l in open("schema.ddl").read().split('\n'):
        add([l])
    add(["insert into users (username, email, password) values (?, ?, ?)", ["alice", "alice@example.com", argon2.hash("password")]])
    add(["insert into users (username, email, password) values (?, ?, ?)", ["bob", "bob@example.com", argon2.hash("bob123")]])
    add(["insert into projects (name, owner) values ('First project', 0)"])
    add(["insert into UserProjects values (1,1)"])
    add(["insert into UserProjects values (1,2)"])
    # alice will be id 1 and bob id 2
    for i in range(20):
        add(["insert into tasks (tid, name, body, priority, due_date, added_date, project) values (?, ?, ?, ?, ?, ?, 1)", [i,
             f"Example Task {i}", f"This is the body text for example task {i}", random.randint(0, 10),
             int(time.time())+random.randint(0, 7*24*60*60), int(time.time()) - random.randint(0, 7 * 24 * 60 * 60)]])

def devrun():
    #file = str(uuid4())+".db"
    file = ":memory:"
    global db
    db = DatabaseActor.start(file)
    fill_tmp_db(db.ask)
    run(host='0.0.0.0', port=8830)

    #os.unlink(file)


if __name__ == '__main__':
    # main("db.db")
    devrun()
