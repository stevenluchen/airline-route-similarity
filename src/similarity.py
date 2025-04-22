import numpy as np
import pickle
import heapq
import json
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
from collections import defaultdict
from pprint import pp

def compute_dtw(vec1, vec2):
    score, _ = fastdtw(vec1, vec2, dist=euclidean)
    return score

def moved_enough(vec, min_displacement_km=100):
    # roughly scaled for lat/lon in degrees (~111 km per deg)
    start = vec.iloc[0, :2]
    end = vec.iloc[-1, :2]
    displacement_deg = np.linalg.norm(end - start)
    displacement_km = displacement_deg * 111  # approximation
    return displacement_km >= min_displacement_km

def top_k_dtw(trunk_vectors, flight_vectors, k=5):
    topk = defaultdict(list)

    for callsign, vec in tqdm(flight_vectors.items(), desc="Flight vectors"):
        alt_start = vec.iloc[0,5]
        alt_end = vec.iloc[-1,5]

        # valid flights must have low starting/ending altitude and traveled at least 100 km
        if alt_start >= 0 or alt_end >= 0 or not moved_enough(vec):
            continue
        
        for i, trunk_vec in enumerate(trunk_vectors):
            score = compute_dtw(vec, trunk_vec)
            # use minheap with negative score to simulate maxheap
            if len(topk[i]) < k:
                heapq.heappush(topk[i], (-score, callsign))
            else:
                heapq.heappushpop(topk[i], (-score, callsign))

    for i in topk:
        topk[i].sort()

    return topk

# load files from /data directory
trunk_vectors = np.load('data/trunk_vectors.npy')
with open("flight_vectors.pkl", "rb") as f:
    flight_vectors = pickle.load(f)
flight_vectors = {k: v for k, v in flight_vectors.items() if v is not None}

topk = top_k_dtw(trunk_vectors, flight_vectors)
pp(topk)

# write results to JSON
trunk_labels = {
    0: "sfo_lax",
    1: "den_ord",
    2: "lax_jfk",
    3: "atl_dfw",
    4: "bos_dca",
    5: "jfk_ord",
    6: "iah_ord",
    7: "sfo_sea",
    8: "mco_atl",
    9: "lax_atl"
}

serializable = {
    trunk_labels[i]: [
        {"callsign": callsign, "dtw_score": -score}
        for score, callsign in sorted(results)
    ]
    for i, results in topk.items()
}

with open("results/topk_dtw.json", "w") as f:
    json.dump(serializable, f, indent=2)

print(f"Saved top-k results to results/topk_dtw.json")