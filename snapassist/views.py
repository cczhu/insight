import flask
import re
from . import app
from . import db
from . import (toronto_longlat, global_min_samples, master_sigma_cut,
               global_max_eps_scaling)
from . import clustering
from . import mapping


bad_css = (r'    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/'
           r'bootstrap/3.2.0/css/bootstrap.min.css"/>\n    <link rel='
           r'"stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/'
           r'3.2.0/css/bootstrap-theme.min.css"/>\n')

@app.route('/')
@app.route('/input')
def input_page():
    return flask.render_template("input.html", err_message="")


def get_search_results(search_term):

    results = db.get_search_results(search_term, table='popular')
    results_background = db.get_search_results(search_term)

    if len(results) < global_min_samples:
        return None

    # Clustering (results is implicitly being altered by clst).
    clst = clustering.Clustering(results, toronto_longlat)
    clst.optics_clustering(global_min_samples=global_min_samples,
                           max_eps_scaling=global_max_eps_scaling)

    # Find cluster outliers and shift them to noise.
    outlier_indices, centroids = clst.get_centroids_and_outliers(
        sigma=master_sigma_cut)
    results.loc[outlier_indices, 'cluster'] = -1

    # Get cluster details to prepare for mapping.
    cluster_info = mapping.ClusterInfo(results, centroids)

    map_TO = mapping.make_map(results, results_background,
                              cluster_info, toronto_longlat)
    return map_TO.get_root()


@app.route('/output')
def map_page():
    search_term = flask.request.args.get('search_keywords')
    # If user leaves the search bar blank, use "CN Tower".
    if search_term == "":
        search_term = "CN Tower"
    map_TO_root = get_search_results(search_term)
    if map_TO_root is None:
        return flask.render_template("input.html", err_message=(
            "Sorry, couldn't find anything with those keywords."))
    map_TO_render = map_TO_root.render()
    # Hack to remove adding redundant bootstrap CSS files.
    map_TO_render = re.sub(bad_css, '', map_TO_render)
    return flask.render_template("output.html", map_TO=map_TO_render)


@app.route('/about')
def about_page():
    return flask.render_template("about.html")
