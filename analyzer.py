from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import linkage, fcluster
import numpy as np

def perform_clustering(df_unit, k_manual=None):
    # 標準化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_unit)

    # PCA（全成分→Kaiser基準で絞り込み）
    pca = PCA()
    X_pca = pca.fit_transform(X_scaled)
    # 固有値1.0以上の成分のみ抽出
    n_components = sum(pca.explained_variance_ >= 1.0)
    X_pca = X_pca[:, :n_components]

    # 階層クラスタリング
    Z = linkage(X_pca, method="ward", metric="euclidean")

    if k_manual:
        k = k_manual
    else:
        distances = Z[:, 2]
        jumps = np.diff(distances)
        search_range = min(10, len(jumps))
        max_jump_idx = np.argmax(jumps[-search_range:-1]) + (len(jumps) - search_range)
        k = len(df_unit) - 1 - max_jump_idx

    clusters = fcluster(Z, t=k, criterion='maxclust')
    return clusters, k
