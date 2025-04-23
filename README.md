# Airline Route Similarity via Trajectory-Based Dynamic Time Warping

This project identifies international analogs to major U.S. trunk routes (e.g. SFO–LAX, LAX–JFK) using a multivariate time series approach applied to real aircraft telemetry. Rather than comparing routes by geography or airline schedule, we focus purely on the behavioral similarity of flights — their shape, structure, and dynamics in the sky.

Built on top of [OpenSky ADS-B data](https://opensky-network.org/data/scientific) and [dynamic time warping](https://cs.fit.edu/~pkc/papers/tdm04.pdf) (DTW), this pipeline processes tens of millions of raw datapoints into interpretable vector forms and surfaces non-obvious analogs such as:

* SFO-LAX ≈ Bahrain-Riyadh
* ORD-LGA ≈ Amsterdam-Warsaw
* ATL-MCO ≈ Kathmandu-Kolkata

---

## Motivation

U.S. domestic airspace is filled with high-density, highly structured trunk routes - but do international equivalents behave the same way? This raises questions like "What’s the SFO–LAX of the Middle East? What’s the LAX–JFK of Europe?"

To do this, we treat each flight as a multivariate trajectory and search globally for the most similar flights to each domestic U.S. trunk route — based purely on telemetry shape.

---

## Method Overview

Data was taken from the OpenSky Network's ADS-B archive for **July 15, 2019**. In total, this consisted of approximately **22,000 filtered, complete flights**. 

Each flight gets encoded as a 200x6 time series. Longer flights get downsampled using interpolation. 

* Latitude and Longitude (displacement from origin, in degrees)
* Altitude and Velocity (standardized across dataset)
* Heading (transformed to `sin(θ)`, `cos(θ)`)

Flights were filtered for:

* Valid commercial callsigns on a major international airline
* Full takeoff/landing arc (starting/ending altitude reading)
* Geographic displacement of over 100 km
* Flight time of less than 8 hours

For 10 unique, significant U.S. trunk routes, we compute an aggregate vector, which gets compared against every international flight using DTW; we retain the most similar analogs per trunk, stored as a dictionary. 

---

## Results & Limitations

For a more detailed summary of methodology, findings, and interpretation, see [report.pdf](https://github.com/stevenluchen/airline-route-similarity/blob/main/report.pdf).

| U.S. Route | Top Analog(s)                                       | Notes                                                                |
|------------|-----------------------------------------------------|----------------------------------------------------------------------|
| SFO-LAX    | Bahrain-Riyadh, Ottawa-Toronto                      | Short, high-frequency corridors connecting nearby economic centers   |
| DEN-ORD    | Kaliningrad-Moscow, London-Berlin, Vienna-Kyiv      | Medium-haul trunk routes connecting key regional hubs                |
| DFW-ATL    | Madrid-Barcelona                                    | Classic domestic shuttle between two dominant national hubs          |
| DCA-BOS    | Amsterdam-Billund, Melbourne-Canberra               | Short-haul flights with balanced climb, cruise, and descent          |
| ORD-LGA    | Amsterdam-Warsaw, Prague-Kyiv, Edinburgh-Copenhagen | Dense intra-European trunk routes with complex ATC routing           |
| LAX-JFK    | San Francisco-Toronto                               | Long-haul eastbound routes with steady cruise and gradual descent    |
| IAH-ORD    | Toulouse-Brussels, Hobart-Sydney, Amsterdam-Ålesund | Lower-visibility pairings with consistent medium-haul structure      |
| ATL-MCO    | Kathmandu-Kolkata, Hamburg-Munich, Zürich-Florence  | Terrain-constrained regional flights with sharp altitude transitions |
| LAX-ATL    | Amsterdam-Moscow, Paris-Kyiv                        | Long-haul transcontinental analogs with deep cruise phase            |

* All comparisons are based on **shape and behavior**, not geography or scheduled times.
* DTW captures **trajectory similarity**, which doesn't always align with traditional airline route maps.
* LAX-JFK often matched SFO-YYZ due to structural similarity, not distance or direction.
* Flights that pass through Chinese airspace suffer from systemic telemetry unreliability, such as sparse coverage and erratic motion patterns, so they were excluded from results on an ad hoc basis. [Here's](https://www.youtube.com/watch?v=sJPxjVASlBc) an interesting YouTube video on it.
