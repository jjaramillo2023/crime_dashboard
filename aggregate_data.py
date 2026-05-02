"""
aggregate_data.py  —  run LOCALLY before deploying
Reads the large CSVs and writes small summary files into data/
"""
import pandas as pd
import geopandas as gpd
from shapely import wkt
import os, json

os.makedirs("data", exist_ok=True)

CHICAGO_FILE  = "/Users/jjaramillo/Downloads/archive/Data/clean/spatial_join_chicago.csv"
SEATTLE_FILE  = "/Users/jjaramillo/Downloads/archive/Data/clean/spatial_join_seattle.csv"
CHICAGO_NEIGH = "/Users/jjaramillo/Downloads/Neighborhoods_chicago.csv"
SEATTLE_NEIGH = "/Users/jjaramillo/Downloads/nma_nhoods_sub.geojson"

CHI_POP = 2_696_555
SEA_POP = 737_255

print("=" * 55)
print("AGGREGATING DATA FOR DASHBOARD")
print("=" * 55)

# ── Load ──────────────────────────────────────────────────────────────
print("\nLoading Chicago data (chunked)…")
chi_cols = ["case_id","year","month","hour","day_of_week",
            "crime_category","arrest_made","domestic","neighborhood"]
chi = pd.concat(
    [c for c in pd.read_csv(CHICAGO_FILE, usecols=chi_cols, chunksize=500_000)],
    ignore_index=True
)
print(f"  Chicago: {len(chi):,} rows")

print("Loading Seattle data…")
sea_cols = ["case_id","year","month","hour","day_of_week",
            "crime_category","shooting_type","neighborhood","large_neighborhood"]
sea = pd.read_csv(SEATTLE_FILE, usecols=sea_cols)
print(f"  Seattle: {len(sea):,} rows")

# ── 1. Overview ───────────────────────────────────────────────────────
print("\n[1/10] Overview…")
overview = pd.DataFrame([
    {
        "city": "Chicago",
        "total_crimes":       len(chi),
        "year_min":           int(chi["year"].min()),
        "year_max":           int(chi["year"].max()),
        "neighborhood_count": int(chi["neighborhood"].nunique()),
        "arrest_rate":        round((chi["arrest_made"] == 1).sum() / len(chi) * 100, 2),
        "domestic_rate":      round((chi["domestic"]    == 1).sum() / len(chi) * 100, 2),
        "population":         CHI_POP,
        "crimes_per_100k":    round(len(chi) / CHI_POP * 100_000, 1),
    },
    {
        "city": "Seattle",
        "total_crimes":       len(sea),
        "year_min":           int(sea["year"].min()),
        "year_max":           int(sea["year"].max()),
        "neighborhood_count": int(sea["neighborhood"].nunique()),
        "arrest_rate":        None,
        "domestic_rate":      None,
        "population":         SEA_POP,
        "crimes_per_100k":    round(len(sea) / SEA_POP * 100_000, 1),
    },
])
overview.to_csv("data/agg_overview.csv", index=False)

# ── 2. By year ────────────────────────────────────────────────────────
print("[2/10] By year…")
def year_agg(df, city, pop):
    g = df.groupby("year").size().reset_index(name="crime_count")
    g["city"] = city
    g["crimes_per_100k"] = (g["crime_count"] / pop * 100_000).round(1)
    return g

by_year = pd.concat([year_agg(chi,"Chicago",CHI_POP),
                     year_agg(sea,"Seattle",SEA_POP)], ignore_index=True)
by_year.to_csv("data/agg_by_year.csv", index=False)

# ── 3. By category ────────────────────────────────────────────────────
print("[3/10] By category…")
chi_cat = chi.groupby("crime_category").agg(
    crime_count=("case_id","count"),
    arrest_count=("arrest_made", lambda x: (x==1).sum())
).reset_index()
chi_cat["city"]          = "Chicago"
chi_cat["pct_of_total"]  = (chi_cat["crime_count"] / len(chi) * 100).round(2)
chi_cat["arrest_rate"]   = (chi_cat["arrest_count"] / chi_cat["crime_count"] * 100).round(2)
chi_cat["crimes_per_100k"] = (chi_cat["crime_count"] / CHI_POP * 100_000).round(1)

sea_cat = sea.groupby("crime_category").agg(
    crime_count=("case_id","count")
).reset_index()
sea_cat["city"]          = "Seattle"
sea_cat["pct_of_total"]  = (sea_cat["crime_count"] / len(sea) * 100).round(2)
sea_cat["arrest_rate"]   = None
sea_cat["crimes_per_100k"] = (sea_cat["crime_count"] / SEA_POP * 100_000).round(1)

by_cat = pd.concat([chi_cat, sea_cat], ignore_index=True)
by_cat.to_csv("data/agg_by_category.csv", index=False)

# ── 4. Hour × Day-of-week heatmap ─────────────────────────────────────
print("[4/10] Hour × day-of-week…")
def hdow_agg(df, city):
    g = df.groupby(["hour","day_of_week"]).size().reset_index(name="crime_count")
    g["city"] = city
    return g

by_hdow = pd.concat([hdow_agg(chi,"Chicago"), hdow_agg(sea,"Seattle")], ignore_index=True)
by_hdow.to_csv("data/agg_by_hour_dow.csv", index=False)

# ── 5. Monthly averages ───────────────────────────────────────────────
print("[5/10] Monthly…")
def month_agg(df, city, pop):
    g = df.groupby("month").size().reset_index(name="crime_count")
    g["city"] = city
    g["avg_per_year"] = (g["crime_count"] / df["year"].nunique()).round(0)
    g["avg_per_100k"] = (g["avg_per_year"] / pop * 100_000).round(1)
    return g

by_month = pd.concat([month_agg(chi,"Chicago",CHI_POP),
                      month_agg(sea,"Seattle",SEA_POP)], ignore_index=True)
by_month.to_csv("data/agg_by_month.csv", index=False)

# ── 6. Chicago neighborhoods ──────────────────────────────────────────
print("[6/10] Chicago neighborhoods…")
chi_nh = chi.dropna(subset=["neighborhood"])
chi_neigh = chi_nh.groupby("neighborhood").agg(
    crime_count=("case_id","count"),
    arrest_rate=("arrest_made", lambda x: round((x==1).sum()/len(x)*100, 2))
).reset_index()
top_cat = (chi_nh.groupby(["neighborhood","crime_category"]).size()
           .reset_index(name="n").sort_values("n",ascending=False)
           .drop_duplicates("neighborhood")[["neighborhood","crime_category"]]
           .rename(columns={"crime_category":"top_category"}))
chi_neigh = chi_neigh.merge(top_cat, on="neighborhood", how="left")
chi_neigh.to_csv("data/agg_chicago_neighborhoods.csv", index=False)

# ── 7. Seattle neighborhoods ──────────────────────────────────────────
print("[7/10] Seattle neighborhoods…")
sea_nh = sea.dropna(subset=["neighborhood"])
sea_neigh = sea_nh.groupby(["neighborhood","large_neighborhood"]).agg(
    crime_count=("case_id","count")
).reset_index()
top_cat_s = (sea_nh.groupby(["neighborhood","crime_category"]).size()
             .reset_index(name="n").sort_values("n",ascending=False)
             .drop_duplicates("neighborhood")[["neighborhood","crime_category"]]
             .rename(columns={"crime_category":"top_category"}))
sea_neigh = sea_neigh.merge(top_cat_s, on="neighborhood", how="left")
sea_neigh.to_csv("data/agg_seattle_neighborhoods.csv", index=False)

# ── 8. Category × year (mix shift) ────────────────────────────────────
print("[8/10] Category × year…")
def cat_year_agg(df, city):
    g = df.groupby(["year","crime_category"]).size().reset_index(name="crime_count")
    g["city"] = city
    g["pct_of_year"] = g.groupby("year")["crime_count"].transform(
        lambda x: (x / x.sum() * 100).round(2))
    return g

cat_year = pd.concat([cat_year_agg(chi,"Chicago"),
                      cat_year_agg(sea,"Seattle")], ignore_index=True)
cat_year.to_csv("data/agg_category_year.csv", index=False)

# ── 9. Seattle shootings ──────────────────────────────────────────────
print("[9/10] Seattle shootings…")
shootings = (sea[sea["shooting_type"].notna() & (sea["shooting_type"].astype(str).str.strip() != "")]
             .groupby(["year","shooting_type"]).size().reset_index(name="crime_count"))
shootings.to_csv("data/agg_seattle_shootings.csv", index=False)

# ── 10. GeoJSON files ─────────────────────────────────────────────────
print("[10/10] GeoJSON files…")

# Chicago — WKT → GeoJSON
chi_raw = pd.read_csv(CHICAGO_NEIGH)
chi_raw["geometry"] = chi_raw["the_geom"].apply(wkt.loads)
chi_geo = gpd.GeoDataFrame(chi_raw[["PRI_NEIGH","geometry"]], crs="EPSG:4326")
chi_geo = chi_geo.rename(columns={"PRI_NEIGH":"neighborhood"})
chi_geo["geometry"] = chi_geo["geometry"].simplify(0.001)
chi_geo.to_file("data/chicago_neighborhoods.geojson", driver="GeoJSON")

# Seattle
sea_geo = gpd.read_file(SEATTLE_NEIGH)[["S_HOOD","L_HOOD","geometry"]]
sea_geo = sea_geo.rename(columns={"S_HOOD":"neighborhood","L_HOOD":"large_neighborhood"})
sea_geo["geometry"] = sea_geo["geometry"].simplify(0.001)
sea_geo.to_file("data/seattle_neighborhoods.geojson", driver="GeoJSON")

print("\n" + "=" * 55)
print("DONE — all files saved to data/")
print("=" * 55)
