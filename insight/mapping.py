import numpy as np
import pandas as pd
import operator
import folium
from matplotlib import colors as mpl_colors
from matplotlib import cm as mpl_cm

paired_cmap = mpl_cm.get_cmap('Paired')


def make_flickr_link(row):
    return 'https://www.flickr.com/photos/{owner}/{photoid}'.format(
        photoid=row['id'], owner=row['owner'])


def make_photo_popup(row, cluster_names):
    popup_html = ('Cluster {cluster}:<br>'
                  '<a href="{link}" target="_blank">'
                  '<img border="0" src="{url}"></a>').format(
        link=make_flickr_link(row), url=row['url_s'],
        cluster=(cluster_names[row['cluster']] if row['cluster'] >= 0 else
                 'background'))
    return popup_html


class Cluster:

    def __init__(self, n_photos, centroid, avg_views, best_photos):
        self.n_photos = operator.index(n_photos)
        self.centroid = centroid
        self.avg_views = avg_views
        self.best_photos = pd.DataFrame(best_photos)


class ClusterInfo:

    best_photo_html = r"""
        <h3>Cluster {name}</h3>
        Number of photos: {n_photos}<br>
        Avg. views per photo: {avg_views}<br>
        Most popular photos:<br>
        <a href="{link}" target="_blank">
        <img border="0" width={width}px src="{pic_url_s}"></a>
        <br>Camera: {camera}<br>
        Lens: {lens}<br>
        Focal Length: {flen}<br>
        Exposure: {exptime}<br>
        F number: {fno}<br>
        ISO: {iso}<br>
    """

    def __init__(self, table, centroids):
        self.table = table

        # Populate clusters.
        self.populate_clusters(centroids)

        # Sort clusters and make name lookup table
        views_over_nphot = [c.avg_views / c.n_photos for c in self.clusters]
        self.cluster_order = list(np.argsort(views_over_nphot) + 1)


    def populate_clusters(self, centroids):
        self.clusters = []
        for i in range(len(centroids)):
            c_cluster = self.table[self.table['cluster'] == i]
            c_n_photos = c_cluster.shape[0]
            c_n_centroid = centroids[i]
            ############## TO DO: Mean or median??? ##################
            # c_n_avg_views = c_cluster['views'].sum() / c_n_photos
            c_n_avg_views = c_cluster['views'].median()
            c_n_best_photos = c_cluster.sort_values(
                'views', ascending=False).iloc[:5, :]
            self.clusters.append(
                Cluster(c_n_photos, c_n_centroid, c_n_avg_views,
                        c_n_best_photos))

    @staticmethod
    def get_cluster_color(cluster_number):
        if cluster_number < 0:
            return '#777777'
        else:
            return mpl_colors.rgb2hex(
                paired_cmap((cluster_number % 12) / 12.)[:3])

    @staticmethod
    def get_camera_or_lens(model):
        if isinstance(model, str):
            if model == "N/A":
                return ''
            return model
        return ''

    @staticmethod
    def get_focal_length(focal_length):
        if focal_length > 0:
            focal_length = "{} mm".format(str(int(focal_length)))
            # if focal_length_35mm > 0:
            #     focal_length_35mm = str(int(focal_length_35mm))
            #     focal_length += " ({} mm at 35mm eqv)".format(
            #         focal_length_35mm)
        else:
            focal_length = ''
        return focal_length

    @staticmethod
    def get_exposure_time(exptime):
        if exptime > 0:
            if exptime >= 1:
                return str(int(exptime)) + " s"
            exptime = str(int(1. / exptime))
            return "1/{} s".format(exptime)
        return ''

    @staticmethod
    def get_fnumber(fnumber):
        if fnumber > 0:
            return "f/{0:.1f}".format(fnumber)
        return ''

    @staticmethod
    def get_iso(iso):
        if iso > 0:
            return "{0:d}".format(int(iso))
        return ''

    def get_cluster_infographic(self, i):
        cluster = self.clusters[i]
        cluster_name = self.cluster_order[i]
        best_photo = cluster.best_photos.iloc[0, :]
        popup_html = self.best_photo_html.format(
            name=cluster_name,
            n_photos=cluster.n_photos,
            avg_views=cluster.avg_views,
            link=make_flickr_link(best_photo),
            pic_url_s=best_photo['url_s'],
            width=min(300, max(250, best_photo['width_s'])),
            camera=self.get_camera_or_lens(best_photo['Camera']),
            lens=self.get_camera_or_lens(best_photo['Lens']),
            flen=self.get_focal_length(best_photo['FocalLength']),
            exptime=self.get_exposure_time(best_photo['FocalLength']),
            fno=self.get_fnumber(best_photo['FNumber']),
            iso=self.get_iso(best_photo['ISO']))

        return cluster.centroid, popup_html


def make_map(results, results_background, cluster_info, default_longlat):

    map_TO = folium.Map(location=(default_longlat.latitude,
                                  default_longlat.longitude),
                        zoom_start=13,
                        tiles='cartodbpositron',
                        width='100%', height='100%')

    # Plot all photos retrieved.
    for (ind, row) in results_background.iterrows():
        folium.CircleMarker((row['latitude'], row['longitude']),
                            radius=0.5, color="#aaa",
                            fill_color="#aaa").add_to(map_TO)

    # Plot clusters.
    results['color'] = [cluster_info.get_cluster_color(item)
                        for item in results['cluster'].values]
    for (ind, row) in results.iterrows():
        folium.CircleMarker((row['latitude'], row['longitude']),
                            popup=make_photo_popup(row,
                                                   cluster_info.cluster_order),
                            radius=(1 if row['cluster'] < 0 else 2),
                            color=row['color'],
                            fill_color=row['color']).add_to(map_TO)

    # Plot best photo in each cluster.
    for i in range(len(cluster_info.clusters)):
        centroid, popup_html = cluster_info.get_cluster_infographic(i)
        folium.map.Marker(centroid[::-1],
                          popup=folium.Popup(html=popup_html, max_width=300),
                          icon=None).add_to(map_TO)

    return map_TO


def make_map_basic(results, results_background, cluster_info, default_longlat):
    """Older version of make_map that doesn't use CSS defined in templates."""

    map_TO = folium.Map(location=(default_longlat.latitude,
                                  default_longlat.longitude),
                        zoom_start=13,
                        tiles='cartodbpositron',
                        width='100%', height='100%')

    # Plot all photos retrieved.
    for (ind, row) in results_background.iterrows():
        folium.CircleMarker((row['latitude'], row['longitude']),
                            radius=0.5, color="#aaa",
                            fill_color="#aaa").add_to(map_TO)

    # Plot clusters.
    results['color'] = [cluster_info.get_cluster_color(item)
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
        Number of photos in cluster {cluster}: {n_incluster}<br>
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
    for cluster in cluster_info.clusters:
        best_photo = cluster.best_photos.iloc[0, :]
        popup_html = best_photo_html.format(
            title=best_photo['title_cleaned'],
            link=make_flickr_link(best_photo),
            cluster=best_photo['cluster'], url=best_photo['url_s'],
            n_incluster=cluster.n_photos)
        if best_photo['FocalLength'] > 0:
            popup_html += best_photo_exif_html.format(
                flen=best_photo['FocalLength'],
                exptime=best_photo['ExposureTime'],
                fno=best_photo['FNumber'],
                iso=best_photo['ISO'])

        folium.map.Marker(cluster.centroid[::-1], popup=popup_html,
                          icon=None).add_to(map_TO)

    return map_TO