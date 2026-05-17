from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import linkage, fcluster
import numpy as np

def perform_clustering(df_unit, k_manual=None):
    # PCAの実行（全成分）
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df_unit)
    pca = PCA()
    pca.fit(df_scaled)

    # 累積寄与率80%以上の成分数を決定
    cumvar = np.cumsum(pca.explained_variance_ratio_)
    n_components = int(np.searchsorted(cumvar, 0.80)) + 1

    # 主成分得点: 生データ × ローディング（SPSSと同じ計算）
    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
    pca_scores = df_unit.values @ loadings[:, :n_components]

    Z = linkage(pca_scores, method="average", metric="euclidean")

    if k_manual:
        k_final = k_manual
    else:
        # 自動決定ロジック
        distances = Z[:, 2]
        jumps = np.diff(distances)
        search_range = min(10, len(jumps))
        max_jump_idx = np.argmax(jumps[-(search_range):-1]) + (len(jumps) - search_range)
        k_final = len(df_unit) - 1 - max_jump_idx

    clusters = fcluster(Z, t=k_final, criterion='maxclust')
    return clusters, k_final