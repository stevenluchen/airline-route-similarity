import pandas as pd
import numpy as np
import pickle
from utils.py import *

master_data = pd.read_parquet("data/opensky_2019-07-15.parquet")

trunk_vectors = []
for r in tqdm(routes, desc = 'Aggregating Trunk Routes'):
    agg = aggregate_route(master_data, r)
    if agg is not None:
        trunk_vectors.append(agg)

np.save('data/trunk_vectors', trunk_vectors)
print(f"Saved trunk aggregates to data/trunk_vectors.npy")

# remove U.S. results from data after trunk vectors have been extracted
us_mask = master_data['callsign'].apply(is_non_us_callsign)
master_data = master_data[us_mask].copy()

flight_vectors = {}
all_callsigns = np.unique(master_data['callsign'])

for c in tqdm(all_callsigns):
    df = extract_flight(master_data, c)
    vec = preprocess_flight(df)
    if vec is not None:
        flight_vectors[c] = vec

# Save clean dictionary
with open('data/flight_vectors.pkl', 'wb') as f:
    pickle.dump(flight_vectors, f)

print(f"Saved {len(flight_vectors)} valid vectors to data/flight_vectors.pkl")