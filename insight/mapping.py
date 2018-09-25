import numpy as np
import folium
from matplotlib import colors as mpl_colors
from matplotlib import cm as mpl_cm

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


plasma_cmap = mpl_cm.get_cmap('plasma')


def get_cluster_color(cluster_number, n_clusters):
    if cluster_number < 0:
        return '#000000'
    else:
        return mpl_colors.rgb2hex(
            plasma_cmap(cluster_number / (n_clusters - 1.))[:3])


class TorontoLongLat:
    """Nominatim long/lat for Toronto, Ontario, Canada."""
    longitude = -79.387207
    latitude = 43.653963


toronto_longlat = TorontoLongLat()


def make_flickr_link(row):
    return 'https://www.flickr.com/photos/{owner}/{photoid}'.format(
        photoid=row['id'], owner=row['owner'])


def simple_clustering(photos_longlat):
    # Feature scaling.
    X = StandardScaler().fit_transform(photos_longlat)

    # https://github.com/alitouka/spark_dbscan/wiki/Choosing-parameters-of-DBSCAN-algorithm
    nbrs = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(X)
    distances, indices = nbrs.kneighbors(X)
    eps = np.percentile(distances[:, 1], 90)
    min_samples = int(0.01 * X.shape[0])

    # Use DBSCAN.
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    return db.labels_


def make_map(results, results_background):

    map_TO = folium.Map(location=(toronto_longlat.latitude,
                                  toronto_longlat.longitude),
                        zoom_start=12,
                        tiles='cartodbpositron',
                        width='100%', height='100%')

    # Plot all photos retrieved.
    for (ind, row) in results_background.iterrows():
        folium.CircleMarker((row['latitude'], row['longitude']),
                            radius=0.5, color="#999999",
                            fill_color="#999999").add_to(map_TO)

    # Plot clusters.
    n_cluster = results['cluster'].max() + 1
    results['color'] = [get_cluster_color(item, n_cluster)
                        for item in results['cluster'].values]
    for (ind, row) in results.iterrows():
        popup_html = ('Cluster {cluster}: <a href="{link}"'
                      'target="_blank">{title}</a>').format(
            title=row['title_cleaned'], link=make_flickr_link(row),
            cluster=row['cluster'])
        folium.CircleMarker((row['latitude'], row['longitude']),
                            popup=popup_html,
                            radius=(1 if row['color'] == '#000000' else 2),
                            color=row['color'],
                            fill_color=row['color']).add_to(map_TO)

    # Plot best photo in each cluster.
    best_photo_html = """
        <h3>Best photo for cluster {cluster}</h3><br>
        <a href="{link}" target="_blank">
        <img border="0" src="{url}"></a>
    """
    best_photo_exif_html = """
        <br> Focal length: {flen}: <br>
        Exposure time: {exptime}: <br>
        F number: {fno}: <br>
        ISO: {iso}: <br>
    """
    for i in range(n_cluster):
        best_idx = results.loc[results['cluster'] == i, 'views'].idxmax()
        best_photo = results.loc[best_idx, :]
        popup_html = best_photo_html.format(
            title=best_photo['title_cleaned'],
            link=make_flickr_link(best_photo),
            cluster=best_photo['cluster'], url=best_photo['url_s'])
        if best_photo['FocalLength'] > 0:
            popup_html += best_photo_exif_html.format(
                flen=best_photo['FocalLength'],
                exptime=best_photo['ExposureTime'],
                fno=best_photo['ExposureTime'],
                iso=best_photo['ISO'])

        folium.map.Marker(best_photo[['latitude', 'longitude']],
                          popup=popup_html, icon=None).add_to(map_TO)

    return map_TO
