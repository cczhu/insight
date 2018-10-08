import numpy as np
import operator

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

import hdbscan
from .sklearn_optics import optics


class Clustering:

    def __init__(self, table, ref_longlat, global_min_samples=10):
        # self.table is a direct link to the pandas table passed, not a view or
        # copy.
        self.table = table
        self.ref_longlat = ref_longlat
        self.longitude_coeff = np.sin(
            self.ref_longlat.latitude * np.pi / 180.)
        self.global_min_samples = operator.index(global_min_samples)

    def feature_scaling(self):
        # Standard feature scaling.
        photos_longlat = self.table[['longitude', 'latitude']].values

        ########### TO DO : REPLACE WITH MANUAL RESCALING?? #############
        X = StandardScaler().fit_transform(photos_longlat)
        # Scale latitude features as a first approximation of great circle
        # distance.
        X[:, 0] *= self.longitude_coeff
        return X

    def dbscan_clustering(self):
        # Feature scaling.
        X = self.feature_scaling()

        # https://github.com/alitouka/spark_dbscan/wiki/Choosing-parameters-of-DBSCAN-algorithm
        nbrs = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(X)
        distances, indices = nbrs.kneighbors(X)
        eps_min = 1e-4 * (np.mean([X[:, 0].max() - X[:, 0].min(),
                                   X[:, 1].max() - X[:, 1].min()]))
        eps = np.max([eps_min, np.percentile(distances[:, 1], 90)])
        min_samples = int(0.01 * X.shape[0])

        # Use DBSCAN.
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
        self.table['cluster'] = db.labels_

    def optics_clustering(self, global_min_samples=10, max_eps_scaling=1.):
        # Feature scaling.
        X = self.feature_scaling()

        min_samples = max([global_min_samples, int(0.01 * X.shape[0])])
        max_eps = max_eps_scaling * np.mean([(X[:, 0].max() - X[:, 0].min()),
                                             (X[:, 1].max() - X[:, 1].min())])

        optcl = optics.OPTICS(min_samples=min_samples, max_eps=max_eps)
        optcl.fit(X)
        self.table['cluster'] = optcl.labels_

    def hdbscan_clustering(self, global_min_samples=10,
                           min_samples_scaling=0.5):
        # Feature scaling.
        X = self.feature_scaling()

        min_cluster_size = max([global_min_samples, int(0.01 * X.shape[0])])

        hdbcl = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size,
                                min_samples=int(min_samples_scaling *
                                                min_cluster_size))
        hdbresult = hdbcl.fit(X)
        self.table['cluster'] = hdbresult.labels_

    def sigma_cut(self, cluster_ll, sigma):
        mean_ll = np.mean(cluster_ll, axis=0)
        xy_dist = cluster_ll - mean_ll
        xy_dist[:, 0] *= self.longitude_coeff
        ll_dist = np.sqrt(np.sum(xy_dist**2, axis=1))
        char_dist = np.percentile(ll_dist, 68.)
        return ll_dist > sigma * char_dist

    def get_centroids_and_outliers(self, sigma=2.5):
        outliers = []
        centroids = []
        for i in range(self.table['cluster'].max() + 1):
            c_cluster = self.table[self.table['cluster'] == i]
            c_cluster_llv = c_cluster.loc[:, ['longitude',
                                              'latitude', 'views']].values
            # Same transform as data cleaning so we're cutting in Euclidean.
            c_outliers = self.sigma_cut(c_cluster_llv[:, :2], sigma)
            outliers += list(c_cluster.index[c_outliers])
            centroids.append(tuple(
                np.average(c_cluster_llv[~c_outliers, :2], axis=0,
                           weights=c_cluster_llv[~c_outliers, 2])))
        return np.sort(np.array(outliers)), centroids
