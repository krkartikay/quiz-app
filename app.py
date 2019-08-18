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


def edit_db(query, args=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    conn.close()
    return True

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def hash_pwd(pwd):
	return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt())


def check_pwd(pwd, hash_):
	return bcrypt.checkpw(pwd.encode('utf-8'), hash_)


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
            flash("You are not logged in!")
            return redirect("/")
    return decorated_function


#############################################################################
#############################################################################

@app.route("/")
def home():
    return render_template("homepage.html")


@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logout")
def logout():
    session['username'] = None
    session['accesslevel'] = None
    flash("Logged out!")
    return redirect("/")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_submit", methods=["POST"])
def register_submit():
    username = request.form['username']
    password = request.form['password']
    verify = request.form['verify']
    if password != verify:
        flash("Passwords do not match!")
        return redirect("/register")
    users = query_db("SELECT * FROM users WHERE username=?", (username,))
    if users:
        flash("User already exists!")
        return redirect("/register")
    edit_db("INSERT INTO users VALUES (?,?,0)", (username, hash_pwd(password)))
    flash("User created sucessfully!")
    return redirect("/")

@app.route("/login_submit", methods=["POST"])
def login_submit():
    username = request.form['username']
    password = request.form['password']
    user = query_db("SELECT * FROM users WHERE username=?", (username,), one=True)
    if user and check_pwd(password, user[1]):
        flash("Logged in!")
        session['username'] = username
        session['accesslevel'] = user[2]
        if session['accesslevel'] == 0:
            return redirect("/quizpage")
        else:
            return redirect("/admin_dashboard")
    else:
        flash("Access Denied!")
        return redirect("/login")

@app.route("/quizpage")
@authorize
def quizpage():
    all_questions = query_db("SELECT * FROM Questions")
    return render_template("quizpage.html", questions = all_questions)


@app.route("/quiz_submit", methods=["POST"])
@authorize
def quiz_submit():
    all_questions = query_db("SELECT * FROM Questions")
    answers = {}
    questions_by_id = {}
    for q in all_questions:
        answers[q[0]] = q[6]
        questions_by_id[q[0]] = q
    score = 0
    for key in request.form:
        q_id = int(key[1:])
        if request.form[key] == answers[q_id]:
            score += int(questions_by_id[q_id][7])


    newID = query_db("SELECT MAX(AttemptID)+1 FROM Scores", one=True)[0]
    if not newID:
        newID = 0

    edit_db("INSERT INTO scores VALUES (?,?,?,?)", (newID, session['username'], score, time.time()))

    return render_template("quiz_submit.html", questions=all_questions, score=score)


@app.route("/admin_dashboard")
@authorize
def admin_dashboard():
    if session['accesslevel'] != 1:
        flash("You are not admin!")
        return redirect("/")
    all_questions = query_db("SELECT * FROM Questions")
    return render_template("admin_dashboard.html", questions = all_questions)


@app.route('/newquestion', methods=["POST"])
@authorize
def newquestion():
    if session['accesslevel'] != 1:
        flash("You are not admin!")
        return redirect("/")
    newID = query_db("SELECT MAX(QID)+1 FROM Questions", one=True)[0]
    if not newID:
        newID = 0
    ques = request.form['ques']
    optA = request.form['optA']
    optB = request.form['optB']
    optC = request.form['optC']
    optD = request.form['optD']
    answer = request.form['answer']
    points = request.form['points']
    edit_db("INSERT INTO Questions VALUES(?,?,?,?,?,?,?,?)",(newID,ques,optA,optB,optC,optD,answer,points))
    return redirect("/admin_dashboard")

app.run(debug=True)
