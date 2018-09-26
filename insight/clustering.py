import numpy as np

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


def dbscan_clustering(photos_longlat):
    # Feature scaling.
    X = StandardScaler().fit_transform(photos_longlat)

    # https://github.com/alitouka/spark_dbscan/wiki/Choosing-parameters-of-DBSCAN-algorithm
    nbrs = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(X)
    distances, indices = nbrs.kneighbors(X)
    eps_min = 1e-4 * (np.mean([X[:, 0].max() - X[:, 0].min(),
                               X[:, 1].max() - X[:, 1].min()]))
    eps = np.max([eps_min, np.percentile(distances[:, 1], 90)])
    min_samples = int(0.01 * X.shape[0])

    # Use DBSCAN.
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    return db.labels_
