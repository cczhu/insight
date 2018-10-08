import numpy as np
import pandas as pd
import operator
import folium
import branca
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


##### Popup HTML (used in ClusterInfo, defined here for clarity) #####

best_photo_html_head = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <title>Bootstrap Example</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
  <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
<style>
.carel-container {
    width: 300px;
    height: 420px;   
}
.carel-image-container {
    width: 300px;
    height: 300px;
    display: table;
    background-color: #000;
}

.carel-image-container .container-align {
    text-align: center;
    vertical-align: middle;
    display: table-cell;
}

.carel-text {
    font-size: 12px;
    color: #000;
    padding-left:20px;
}

.carousel-control {
  color: #ffc700;
  opacity: 1;
  background:none;
}

.carousel-indicators .active{
    background-color: #f00;
}
</style>
</head>
<body>
"""

best_photo_html_tail = r"""<h3>Cluster {name}</h3>
Number of photos: {n_photos}<br>
Avg. views per photo: {avg_views}<br><br>
<div id="myCarousel" class="carousel slide" data-ride="carousel" data-interval=false>
 <div class="carousel-inner">
{carousel_elements}
 </div>
 <a class="left carousel-control" href="#myCarousel" data-slide="prev" style="background:none">
   <span class="glyphicon glyphicon-chevron-left"></span>
   <span class="sr-only">Previous</span>
 </a>
 <a class="right carousel-control" href="#myCarousel" data-slide="next" style="background:none">
   <span class="glyphicon glyphicon-chevron-right"></span>
   <span class="sr-only">Next</span>
 </a>
</div>
</body>
</html>"""

best_photo_html_element = r"""  <div class="item{active} carel-container">
   <a href="{link}" target="_blank">
   <div class='carel-image-container'>
   <div class="container-align">
   <img src="{pic_url_s}" style="width:{imgwidth}px; height:{imgheight}px;">
   </div>
   </div>
   </a>
   <div class='carel-text'>
   <br>Camera: {camera}<br>
   Lens: {lens}<br>
   Focal Length: {flen}<br>
   Exposure: {exptime}<br>
   F number: {fno}<br>
   ISO: {iso}<br>
   </div>
  </div>"""

##### Popup HTML (used in ClusterInfo, defined here for clarity) #####


class Cluster:

    def __init__(self, n_photos, centroid, avg_views, best_photos):
        self.n_photos = operator.index(n_photos)
        self.centroid = centroid
        self.avg_views = avg_views
        self.best_photos = pd.DataFrame(best_photos)


class ClusterInfo:
    """Class to calculate cluster information presentation.

    Includes methods for creating Folium map popup HTML (using classes defined
    in snapassist.css).  Popup size is hardcoded in accordance with the CSS
    file.
    """

    # Currently hardcoded in CSS, so hardcode it here.
    popup_width = 300

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

    def scale_image_to_frame(self, width, height):
        """Scale Flickr url_s image to fit Folium popup.

        Popup shape is hard-coded as `self.popup_width` in both length and
        height.  Function rescales so that the long axis exactly fits within
        this box.
        """
        aspect = width / height
        # Image is landscape.
        if aspect >= 1:
            scale = self.popup_width / width
            return (self.popup_width, int(scale * height))
        # Otherwise image is portrait.
        scale = self.popup_width / height
        return (int(scale * width), self.popup_width)

    def get_carousel(self, row, first=False):
        imgwidth, imgheight = self.scale_image_to_frame(row['width_s'],
                                                        row['height_s'])
        if first:
            active = " active"
        else:
            active = ""
        return best_photo_html_element.format(
            pic_url_s=row['url_s'],
            active=active,
            boxl=self.popup_width,
            imgwidth=imgwidth,
            imgheight=imgheight,
            link=make_flickr_link(row),
            camera=self.get_camera_or_lens(row['Camera']),
            lens=self.get_camera_or_lens(row['Lens']),
            flen=self.get_focal_length(row['FocalLength']),
            exptime=self.get_exposure_time(row['FocalLength']),
            fno=self.get_fnumber(row['FNumber']),
            iso=self.get_iso(row['ISO']))

    def get_cluster_infographic(self, i):
        cluster = self.clusters[i]
        cluster_name = self.cluster_order[i]

        carousel_elements = ""
        for i, (ind, row) in enumerate(cluster.best_photos.iterrows()):
            if i == 0:
                carousel_elements += self.get_carousel(row, first=True) + "\n"
            else:
                carousel_elements += self.get_carousel(row) + "\n"

        popup_html = best_photo_html_tail.format(
            name=cluster_name,
            n_photos=cluster.n_photos,
            avg_views=int(cluster.avg_views),
            carousel_elements=carousel_elements)

        return cluster.centroid, best_photo_html_head + '\n' + popup_html

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
        iframe = branca.element.IFrame(html=popup_html, width=300, height=550)
        popup = folium.Popup(iframe, max_width=300)
        folium.map.Marker(centroid[::-1], popup=popup,
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