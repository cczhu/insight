import flask
from . import app
from . import db


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World! This is a test of the thing {x}".format(
        x=db.mtab.shape[0])


@app.route('/db')
def birth_page():
    return db.mtab.iloc[0:10, :].to_html()


@app.route('/db_fancy')
def cesareans_page_fancy():
    return flask.render_template('cesarians.html',
                                 title="I WANT MY TITLE",
                                 mytable=db.mtab.iloc[0:3, :].to_html())


@app.route('/input')
def cesareans_input():
    return flask.render_template("input.html")


@app.route('/output')
def cesareans_output():
    patient = flask.request.args.get('birth_month')
    return flask.render_template("output.html", births=patient,
                                 the_result='test')
