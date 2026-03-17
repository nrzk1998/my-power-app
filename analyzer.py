from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import linkage, fcluster
import numpy as np

def perform_clustering(df_unit, k_manual=None):
    scaler = StandardScaler()
    X_std = scaler.fit_transform(df_unit)

    # PCAの実行（全成分）
    pca = PCA()
    pca_scores_full = pca.fit_transform(X_std)
    
    # 固有値1.0以上の成分のみ抽出
    n_components = sum(pca.explained_variance_ >= 1.0)
    pca_scores = pca_scores_full[:, :n_components] 

    Z = linkage(pca_scores, method="ward", metric="euclidean")

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