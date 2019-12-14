# pyth
# by python-b5
#
# A simple link shortener made with Python and Flask.

from flask import Flask, render_template, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from validator_collection import checkers
import itertools
import string
import random
import os

project_dir = os.path.dirname(os.path.abspath(__file__))

application = Flask(__name__)
application.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(project_dir, 'links.db')
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(application)
migrate = Migrate(application, db)

class Link(db.Model):
    link = db.Column(db.String(80), unique=True, nullable=False, primary_key=True)
    target = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80))

    def __repr__(self):
        return "<Link: {}>".format(self.link)

illegal_links = ["__repl", "peek", "decoder", "toggle-peek", "make", "delete", "change-link", "change-target", "decode"]

def make_url():
    length = 3
    tried = []
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits

    done = False
    while not done:
        chosen = False
        while not chosen:
            link = ''.join(random.choices(chars, k=length))
            chosen = link not in tried
        
        tried.applicationend(link)
        if Link.query.filter(Link.link == tried[-1]).first():
            length += 1
            tried = []
        elif tried == itertools.combinations(chars, length):
            done = True
    
    return tried[-1]

@application.shell_context_processor
def make_shell_context():
    return {'db': db, 'Link': Link}

@application.route('/<page>')
def go_to_page(page):
    if request.cookies.get("peek") == "1":
        return redirect("peek/" + page)
    else:
        try:
            target = Link.query.get(page).target
            return redirect(target, 301)
        except:
            return render_template("error.html") 

@application.route('/<page>/<extra>')
def go_to_page_extra(page, extra):
    if request.cookies.get("peek") == "1":
        return redirect("/peek/" + page + "/" + extra)
    else:
        try:
            target = Link.query.get(page).target
            if extra:
                if target[-1] != "/":
                    target += "/"
                target += extra
            return redirect(target, 301)
        except:
            return render_template("error.html") 

@application.route('/peek/<page>')
def peek_page(page):
    try:
        target = Link.query.get(page).target
        return render_template("peek.html", link=page, target=target)
    except:
        return render_template("error.html")

@application.route('/peek/<page>/<extra>')
def peek_page_extra(page, extra):
    try:
        target = Link.query.get(page).target
        if extra:
            if target[-1] != "/":
                target += "/"
            target += extra
        return render_template("peek.html", link=page, target=target)
    except:
        return render_template("error.html") 

@application.route('/')
def index():
	return render_template('index.html', peek="On" if request.cookies.get("peek") == "1" else "Off")

@application.route('/decoder')
def decode():
    return render_template('decode.html')

@application.route('/toggle-peek')
def toggle_peek():
    resp = make_response(redirect("https://www.pyth.link"))
    if request.cookies.get("peek") in (None, "0"):
        resp.set_cookie("peek", "1")
    elif request.cookies.get("peek") == "1":
        resp.set_cookie("peek", "0")
    return resp

@application.route('/make', defaults={'target': None, 'link': None, 'password': None})
def make_link(target, link, password):  
    if link == None:
        link = request.args.get('link') 
    if target == None:
        target = request.args.get('target')
    if password == None:
        password = request.args.get('password')
    if (not target.startswith("http://")) and (not target.startswith("https://")):
        target = "http://" + target
    if not ((link.isalnum() or not link) and password and checkers.is_url(target)):
        return render_template("input_error.html")
    if Link.query.get(link) or link in illegal_links:
        return render_template("taken.html")
    else:
        if not link:
            link = make_url()
        l = Link(link=link, target=target, password=password)
        db.session.add(l)
        db.session.commit()
        return render_template("created.html", link=link, password=password)

@application.route('/delete', defaults={'link': None, 'password': None})
def delete_link(link, password):   
    if link == None:
        link = request.args.get('link')
    if password == None:
        password = request.args.get('password')
    if not (link and password):
        return render_template("input_error.html")
    try:
        password_real = Link.query.get(link).password
        if password == str(password_real):
            Link.query.get(link).delete()
            db.session.commit()
            return render_template("removed.html")
        else:
            return render_template("wrong.html")
    except:
        return render_template("error.html")

@application.route('/change-link', defaults={'link': None, 'password': None, 'new_link': None})
def change_link(link, password, new_link):   
    if link == None:
        link = request.args.get('link')
    if password == None:
        password = request.args.get('password')
    if new_link == None:
        new_link = request.args.get('new_link')
    if not new_link:
        new_link = make_url()
    if not ((link.isalnum() or not link) and password):
        return render_template("input_error.html")
    try:
        password_real = Link.query.get(link).password
        if password == str(password_real) and not Link.query.get(new_link):
            Link.query.get(link).link = new_link
            return render_template("changed.html")
        elif password != str(password_real):
            return render_template("wrong.html")
        elif Link.query.get(link) or link in illegal_links:
            return render_template("taken.html")
    except:
        return render_template("error.html")

@application.route('/change-target', defaults={'link': None, 'password': None, 'new_target': None})
def change_target(link, password, new_target):   
    if link == None:
        link = request.args.get('link')
    if password == None:
        password = request.args.get('password')
    if new_target == None:
        new_target = request.args.get('new_target')
    if (not new_target.startswith("http://")) and (not new_target.startswith("https://")):
        new_target = "http://" + new_target
    if not (link and password and checkers.is_url(new_target)):
        return render_template("input_error.html")
    try:
        password_real = Link.query.get(link).password
        if password == str(password_real):
            Link.query.get(link).link = new_link
            return render_template("changed.html")
        else:
            return render_template("wrong.html")
    except:
        return render_template("error.html")

@application.route('/decode', defaults={'link': None})
def decode_link(link):
    try:
        if link == None:
            link = request.args.get('link')
        if not link:
            return render_template("input_error.html")
        target = Link.query.get(link).target
        return render_template("decoded.html", target=target)
    except:
        return render_template("error.html")

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8080)