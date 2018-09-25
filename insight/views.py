import flask
from . import app
from . import db
from . import clustering
from . import mapping


@app.route('/')
@app.route('/input')
def input_page():
    return flask.render_template("input.html", err_message="")


@app.route('/output')
def map_page():
    search_term = flask.request.args.get('search_keywords')
    results = db.get_search_results(search_term, table='popular')
    results_background = db.get_search_results(search_term)

    if len(results) == 0:
        return flask.render_template("input.html", err_message=(
            "Sorry, couldn't find anything with those keywords."))

    results['cluster'] = clustering.dbscan_clustering(
        results[['longitude', 'latitude']].values)

    map_TO = mapping.make_map(results, results_background)
    map_TO_str = map_TO.get_root().render()

    return flask.render_template("output.html", map_TO=map_TO_str)


@app.route('/about')
def about_page():
    return flask.render_template("about.html")
