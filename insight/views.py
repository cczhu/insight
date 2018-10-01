import flask
from . import app
from . import db
from . import (toronto_longlat, global_min_samples, master_sigma_cut,
               global_max_eps_scaling)
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

    if len(results) < global_min_samples:
        return flask.render_template("input.html", err_message=(
            "Sorry, couldn't find anything with those keywords."))

    # Clustering (results is implicitly being altered by clst).
    clst = clustering.Clustering(results, toronto_longlat)
    clst.optics_clustering(global_min_samples=global_min_samples,
                           max_eps_scaling=global_max_eps_scaling)

    # Find cluster outliers and shift them to noise.
    outlier_indices, centroids = clst.get_centroids_and_outliers(
        sigma=master_sigma_cut)
    results.loc[outlier_indices, 'cluster'] = -1

    map_TO = mapping.make_map(results, results_background, toronto_longlat)
    map_TO_str = map_TO.get_root().render()

    return flask.render_template("output.html", map_TO=map_TO_str)


@app.route('/about')
def about_page():
    return flask.render_template("about.html")
