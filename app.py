import time
import sqlite3
import bcrypt
from flask import *
from functools import wraps

app = Flask(__name__)

app.secret_key = "secret!"

DATABASE = "db.sqlite"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def hash_pwd(pwd):
	return bcrypt.hashpw(pwd.encode('utf-8'), gensalt())


def check_pwd(pwd, hash_):
	return bcrypt.checkpw(pwd.encode('utf-8'), hash_.encode('utf-8'))


def make_error(status_code, message):
    response = jsonify({
        'status': status_code,
        'error': message,
    })
    # response.status_code = status_code
    return response


def authorize(f):
    @wraps(f)
    def decorated_function(*args, **kws):
    	if 'username' in session and session['username'] != None:
    		return f(*args, **kws)
    	else:
    		return make_error(401, "Need to be loggedin")
    return decorated_function


#############################################################################
#############################################################################

@app.route("/")
def home():
    return render_template("homepage.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_submit", methods=["POST"])
def register_submit():
    pass


@app.route("/login_submit", methods=["POST"])
def login_submit():
    pass

@authorize
@app.route("/quizpage")
def quizpage():
    return render_template("quizpage.html")


@authorize
@app.route("/admin_dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")


