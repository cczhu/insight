import numpy as np
import operator

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

import hdbscan
from .sklearn_optics import optics


class Clustering:

    def __init__(self, table, ref_longlat, global_min_samples=15):
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

        X = StandardScaler().fit_transform(photos_longlat)
        # Scale longitude features as a first approximation of great circle
        # distance.
        X[:, 0] *= self.longitude_coeff
        return X

    def dbscan_clustering(self):
        # Feature scaling.
        X = self.feature_scaling()

        # Setting eps and min_samples based on
        # https://github.com/alitouka/spark_dbscan/wiki/Choosing-parameters-of-DBSCAN-algorithm
        nbrs = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(X)
        distances, indices = nbrs.kneighbors(X)
        eps_min = 1e-4 * (np.mean([X[:, 0].max() - X[:, 0].min(),
                                   X[:, 1].max() - X[:, 1].min()]))
        eps = np.max([eps_min, np.percentile(distances[:, 1], 90)])
        min_samples = int(0.005 * X.shape[0])

        # Use DBSCAN.
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
        self.table['cluster'] = db.labels_

    def optics_clustering(self, max_eps_scaling=1.):
        # Feature scaling.
        X = self.feature_scaling()

        min_samples = max([self.global_min_samples, int(0.005 * X.shape[0])])
        max_eps = max_eps_scaling * np.mean([(X[:, 0].max() - X[:, 0].min()),
                                             (X[:, 1].max() - X[:, 1].min())])

        optcl = optics.OPTICS(min_samples=min_samples, max_eps=max_eps)
        optcl.fit(X)
        self.table['cluster'] = optcl.labels_

    def hdbscan_clustering(self, min_samples_scaling=0.5):
        # Feature scaling.
        X = self.feature_scaling()

        min_cluster_size = max([self.global_min_samples,
                                int(0.005 * X.shape[0])])

        hdbcl = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size,
                                min_samples=int(min_samples_scaling *
                                                min_cluster_size))
        hdbresult = hdbcl.fit(X)
        self.table['cluster'] = hdbresult.labels_

    def _sigma_trim(self, cluster_ll, sigma, critical_char_dist):
        """Perform sigma cut to trim outliers from clusters.

        The median long/lat is used as an estimate of the true cluster
        centroid.  Once found, the 68th percentile characteristic distance
        `char_dist` is found.  Points further than `sigma * char_dist` away
        from the median are clipped (eg. if sigma = 2.5, points 2.5 deviations
        away and beyond are clipped).

        If `char_dist` is larger than `critical_char_dist`, the entire cluster
        is removed.
        """

        med_ll = np.median(cluster_ll, axis=0)
        xy_dist = cluster_ll - med_ll
        # Same transform as data cleaning so we're cutting in Euclidean.
        xy_dist[:, 0] *= self.longitude_coeff
        ll_dist = np.sqrt(np.sum(xy_dist**2, axis=1))

        char_dist = np.percentile(ll_dist, 68.)

        if critical_char_dist and (char_dist > critical_char_dist):
            return np.ones_like(ll_dist, dtype=bool)
        return ll_dist > sigma * char_dist

    def trim_and_get_centroids(self, sigma=2.5, critical_views=False,
                               critical_char_dist=False):
        """Cluster trimmer, to get rid of outliers and bad clusters.

        This method first checks to see if there's at least one photo that
        ranks in the 25% most popular in terms of views.  If so, it prunes
        cluster outliers using sigma clipping, eliminating any clusters that
        are too diffuse.

        Since this

        Parameters
        ----------
        sigma : float, optional
            Sigma for pruning.  Default: 2.5.
        critical_views : float or None, optional
            Critical number of views at least one of the photos in the cluster
            must have for it to be relevant.  If `None` (default), the check is
            skipped.
        critical_char_dist : float or None, optional
            Critical characteristic distance - see discussion in `_sigma_trim`.
            If `None` (default), the check is skipped.

        Returns
        -------
        outliers : numpy.ndarray
            Array of sorted elements.
        ids : list
            List of cluster IDs corresponding to values in
            `self.table['cluster']`. Any clusters in `self.table['cluster']`
            whose elements are all in `outliers` is removed from the list.
        centroids : list
            Corresponding centroids for clusters in `ids`.
        """

        outliers = []
        ids = []
        centroids = []

        for i in range(self.table['cluster'].max() + 1):
            c_cluster = self.table[self.table['cluster'] == i]

            c_cluster_llv = c_cluster.loc[:, ['longitude',
                                              'latitude', 'views']].values
            c_outliers = self._sigma_trim(c_cluster_llv[:, :2], sigma,
                                          critical_char_dist)

            # If, following sigma clipping, the max number of views of any
            # photo in the remaining cluster is too low, remove the whole
            # cluster.
            if critical_views and (len(c_cluster[~c_outliers]) > 0):
                if c_cluster.loc[~c_outliers, 'views'].max() < critical_views:
                    c_outliers = np.ones(len(c_cluster), dtype=bool)

            # Add outliers (possibly the whole cluster to the global list).
            c_outlier_indices = list(c_cluster.index[c_outliers])
            outliers += c_outlier_indices

            # If we didn't add the whole cluster, append the cluster ID and
            # centroid.
            if len(c_outlier_indices) < len(c_cluster):
                ids.append(i)
                centroids.append(tuple(
                    np.average(c_cluster_llv[~c_outliers, :2], axis=0,
                               weights=c_cluster_llv[~c_outliers, 2])))
        return np.sort(np.array(outliers)), ids, centroids