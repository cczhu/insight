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
