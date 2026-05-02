import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

st.set_page_config(
    page_title="Crime Analytics | Chicago × Seattle",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Constants ─────────────────────────────────────────────────────────
CHI_COLOR  = "#FF6B35"
SEA_COLOR  = "#4ECDC4"
CHI_POP    = 2_696_555
SEA_POP    = 737_255
TEMPLATE   = "plotly_dark"
DOW_ORDER  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
MONTH_MAP  = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
              7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

CAT_COLORS = {
    "Theft":"#3498DB", "Assault":"#E74C3C", "Burglary":"#E67E22",
    "Vehicle Theft":"#9B59B6", "Vandalism":"#1ABC9C", "Drugs":"#F39C12",
    "Robbery":"#C0392B", "Fraud":"#2ECC71", "Weapons":"#95A5A6",
    "Sex Offenses":"#D35400", "Homicide":"#ECF0F1", "Arson":"#F8C471",
    "Public Disorder":"#7F8C8D", "Trespassing":"#27AE60",
    "Domestic / Family":"#F1948A", "Offenses Involving Minors":"#D7DBDD",
    "Public Corruption":"#85C1E9", "Kidnapping":"#8E44AD",
    "Human Trafficking":"#2980B9", "Prostitution":"#FADBD8",
    "Gambling":"#A9CCE3", "Other":"#566573",
}

# ── CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0e1117; }
.hero-title {
    font-size: 2.8rem; font-weight: 900; letter-spacing: -1px;
    background: linear-gradient(90deg, #FF6B35 30%, #4ECDC4 70%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { color: #888; font-size: 1rem; margin-top: -10px; margin-bottom: 20px; }
.stat-card {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px; padding: 22px 16px; text-align: center;
}
.stat-val  { font-size: 2.1rem; font-weight: 800; color: #4ECDC4; line-height: 1; }
.stat-lbl  { font-size: 0.78rem; color: #777; margin-top: 6px; letter-spacing: .5px; text-transform: uppercase; }
.section-label { font-size: 0.72rem; color: #555; text-transform: uppercase;
                 letter-spacing: 1px; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────
@st.cache_data
def load():
    overview  = pd.read_csv("data/agg_overview.csv")
    by_year   = pd.read_csv("data/agg_by_year.csv")
    by_cat    = pd.read_csv("data/agg_by_category.csv")
    by_hdow   = pd.read_csv("data/agg_by_hour_dow.csv")
    by_month  = pd.read_csv("data/agg_by_month.csv")
    chi_neigh = pd.read_csv("data/agg_chicago_neighborhoods.csv")
    sea_neigh = pd.read_csv("data/agg_seattle_neighborhoods.csv")
    cat_year  = pd.read_csv("data/agg_category_year.csv")
    shootings = pd.read_csv("data/agg_seattle_shootings.csv")
    with open("data/chicago_neighborhoods.geojson") as f: chi_geo = json.load(f)
    with open("data/seattle_neighborhoods.geojson") as f: sea_geo = json.load(f)
    return overview,by_year,by_cat,by_hdow,by_month,chi_neigh,sea_neigh,cat_year,shootings,chi_geo,sea_geo

overview,by_year,by_cat,by_hdow,by_month,chi_neigh,sea_neigh,cat_year,shootings,chi_geo,sea_geo = load()
chi_ov = overview[overview["city"]=="Chicago"].iloc[0]
sea_ov = overview[overview["city"]=="Seattle"].iloc[0]
total  = int(chi_ov["total_crimes"]) + int(sea_ov["total_crimes"])
year_span = f"{min(int(chi_ov['year_min']),int(sea_ov['year_min']))}–{max(int(chi_ov['year_max']),int(sea_ov['year_max']))}"

# ── Hero ──────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">Crime Analytics Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Chicago × Seattle · Urban Crime Patterns · Big Data Analysis</p>', unsafe_allow_html=True)

c1,c2,c3,c4,c5 = st.columns(5)
cards = [
    (f"{total:,}",          "Crime Records Analyzed"),
    (year_span,             "Years Covered"),
    ("2",                   "Major US Cities"),
    (f"{int(chi_ov['neighborhood_count'])+int(sea_ov['neighborhood_count'])}",
                            "Neighborhoods Mapped"),
    ("8.3M+",               "Raw Data Points"),
]
for col,(val,lbl) in zip([c1,c2,c3,c4,c5], cards):
    col.markdown(f'<div class="stat-card"><div class="stat-val">{val}</div>'
                 f'<div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["City Comparison", "Chicago", "Seattle"])


# ══════════════════════════════════════════════════════════════════════
#  TAB 1 — COMPARISON
# ══════════════════════════════════════════════════════════════════════
with tab1:

    # KPI row
    st.markdown('<p class="section-label">Normalized per 100,000 residents — total period</p>', unsafe_allow_html=True)
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Chicago — Crime Rate",  f"{chi_ov['crimes_per_100k']:,.0f} /100k")
    k2.metric("Seattle — Crime Rate",  f"{sea_ov['crimes_per_100k']:,.0f} /100k",
              delta=f"{sea_ov['crimes_per_100k']-chi_ov['crimes_per_100k']:+,.0f} vs Chicago")
    k3.metric("Chicago — Arrest Rate", f"{chi_ov['arrest_rate']:.1f}%")
    k4.metric("Chicago — Domestic %",  f"{chi_ov['domestic_rate']:.1f}%",
              help="% of crimes flagged as domestic incidents (Seattle data does not include this field)")

    st.markdown("---")

    # ── Crime rate trend ──────────────────────────────────────────────
    st.subheader("Crime Rate Over Time  (per 100,000 residents)")
    sea_start = int(by_year[by_year["city"]=="Seattle"]["year"].min())
    trend = by_year[by_year["year"] >= sea_start].copy()

    fig = px.line(trend, x="year", y="crimes_per_100k", color="city",
                  color_discrete_map={"Chicago":CHI_COLOR,"Seattle":SEA_COLOR},
                  template=TEMPLATE, markers=True,
                  labels={"crimes_per_100k":"Crimes per 100k residents","year":"Year","city":"City"})
    fig.add_vline(x=2020, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                  annotation_text="COVID-19", annotation_font_color="#aaa", annotation_position="top left")
    fig.update_layout(height=420, legend=dict(x=0.01,y=0.99,bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, use_container_width=True)

    # ── Category breakdown ────────────────────────────────────────────
    st.subheader("Crime Category Breakdown  (per 100,000 residents)")
    cat_cmp = by_cat[by_cat["crime_category"]!="Other"].copy()
    cat_cmp = cat_cmp.sort_values("crimes_per_100k", ascending=False)

    fig = px.bar(cat_cmp, x="crime_category", y="crimes_per_100k", color="city",
                 barmode="group",
                 color_discrete_map={"Chicago":CHI_COLOR,"Seattle":SEA_COLOR},
                 template=TEMPLATE,
                 labels={"crimes_per_100k":"Crimes per 100k","crime_category":"Category","city":"City"})
    fig.update_layout(height=430, xaxis_tickangle=-35,
                      legend=dict(x=0.01,y=0.99,bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, use_container_width=True)

    # ── Heatmaps ──────────────────────────────────────────────────────
    st.subheader("When Do Crimes Happen?  (Hour × Day of Week — % share)")
    hcol1, hcol2 = st.columns(2)

    for col, city, cscale, label in [
        (hcol1, "Chicago", [[0,"#1a0a00"],[1,"#FF6B35"]], "Chicago"),
        (hcol2, "Seattle", [[0,"#001a19"],[1,"#4ECDC4"]], "Seattle"),
    ]:
        with col:
            st.markdown(f"**{label}**")
            hdow = by_hdow[by_hdow["city"]==city].copy()
            hdow["pct"] = hdow["crime_count"] / hdow["crime_count"].sum() * 100
            pivot = hdow.pivot_table(index="day_of_week", columns="hour",
                                     values="pct", aggfunc="sum")
            pivot = pivot.reindex([d for d in DOW_ORDER if d in pivot.index])
            fig = go.Figure(go.Heatmap(
                z=pivot.values,
                x=[f"{h}:00" for h in pivot.columns],
                y=pivot.index.tolist(),
                colorscale=cscale,
                hovertemplate="Hour: %{x}<br>Day: %{y}<br>Share: %{z:.3f}%<extra></extra>",
                showscale=False,
            ))
            fig.update_layout(template=TEMPLATE, height=310,
                              xaxis_title="Hour of day", yaxis_title="",
                              margin=dict(l=0,r=0,t=10,b=40))
            st.plotly_chart(fig, use_container_width=True)

    # ── Seasonal ──────────────────────────────────────────────────────
    st.subheader("Seasonal Patterns  (average crimes per month, per 100k residents)")
    sea_monthly = by_month.copy()
    sea_monthly["month_name"] = sea_monthly["month"].map(MONTH_MAP)

    fig = px.line(sea_monthly, x="month_name", y="avg_per_100k", color="city",
                  color_discrete_map={"Chicago":CHI_COLOR,"Seattle":SEA_COLOR},
                  template=TEMPLATE, markers=True,
                  labels={"avg_per_100k":"Avg crimes/month per 100k","month_name":"Month","city":"City"})
    fig.update_layout(height=380,
                      xaxis=dict(categoryorder="array",
                                 categoryarray=list(MONTH_MAP.values())),
                      legend=dict(x=0.01,y=0.99,bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
#  TAB 2 — CHICAGO
# ══════════════════════════════════════════════════════════════════════
with tab2:

    map_col, stat_col = st.columns([3,1])

    with stat_col:
        st.markdown("### Chicago")
        st.metric("Total Crimes",    f"{int(chi_ov['total_crimes']):,}")
        st.metric("Period",          f"{int(chi_ov['year_min'])}–{int(chi_ov['year_max'])}")
        st.metric("Neighborhoods",   int(chi_ov["neighborhood_count"]))
        st.metric("Arrest Rate",     f"{chi_ov['arrest_rate']:.1f}%")
        st.metric("Domestic Rate",   f"{chi_ov['domestic_rate']:.1f}%")
        st.metric("Population",      f"{CHI_POP:,}")
        st.metric("Crime Rate",      f"{chi_ov['crimes_per_100k']:,.0f} /100k")

    with map_col:
        st.subheader("Crime Count by Neighborhood")
        fig = px.choropleth_mapbox(
            chi_neigh,
            geojson=chi_geo,
            locations="neighborhood",
            featureidkey="properties.neighborhood",
            color="crime_count",
            color_continuous_scale="Reds",
            mapbox_style="carto-darkmatter",
            zoom=9.5,
            center={"lat":41.83,"lon":-87.65},
            opacity=0.8,
            hover_name="neighborhood",
            hover_data={"crime_count":True,"arrest_rate":True,"top_category":True,"neighborhood":False},
            labels={"crime_count":"Total Crimes","arrest_rate":"Arrest Rate %","top_category":"Top Crime"},
            template=TEMPLATE,
        )
        fig.update_layout(height=520, margin=dict(r=0,t=0,l=0,b=0),
                          coloraxis_colorbar=dict(title="Crimes",tickfont=dict(color="#aaa")))
        st.plotly_chart(fig, use_container_width=True)

    # Neighborhood rankings
    st.subheader("Neighborhood Rankings")
    r1, r2 = st.columns(2)

    with r1:
        st.markdown("**Top 10 — Most Crimes**")
        top10 = chi_neigh.nlargest(10,"crime_count").sort_values("crime_count")
        fig = px.bar(top10, x="crime_count", y="neighborhood", orientation="h",
                     template=TEMPLATE, color_discrete_sequence=[CHI_COLOR],
                     text="crime_count",
                     labels={"crime_count":"Total Crimes","neighborhood":""})
        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig.update_layout(height=380, showlegend=False, xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

    with r2:
        st.markdown("**Bottom 10 — Safest Neighborhoods**")
        bot10 = chi_neigh.nsmallest(10,"crime_count").sort_values("crime_count",ascending=False)
        fig = px.bar(bot10, x="crime_count", y="neighborhood", orientation="h",
                     template=TEMPLATE, color_discrete_sequence=["#2ECC71"],
                     text="crime_count",
                     labels={"crime_count":"Total Crimes","neighborhood":""})
        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig.update_layout(height=380, showlegend=False, xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

    # Long trend with annotations
    st.subheader("Chicago Crime Trend 2001–2024")
    chi_yr = by_year[by_year["city"]=="Chicago"]
    fig = px.area(chi_yr, x="year", y="crime_count",
                  template=TEMPLATE, color_discrete_sequence=[CHI_COLOR],
                  labels={"crime_count":"Total Crimes","year":"Year"})
    for xv, txt, pos in [
        (2008,"2008 Financial Crisis","top right"),
        (2016,"2016 Homicide Spike","top left"),
        (2020,"COVID-19","top right"),
    ]:
        fig.add_vline(x=xv, line_dash="dash", line_color="rgba(255,255,255,0.25)",
                      annotation_text=txt, annotation_font_color="#aaa",
                      annotation_font_size=10, annotation_position=pos)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Category mix shift
    st.subheader("How Has the Crime Mix Changed?  (% of crimes per year)")
    chi_cy = cat_year[cat_year["city"]=="Chicago"]
    top8 = chi_cy.groupby("crime_category")["crime_count"].sum().nlargest(8).index
    chi_cy = chi_cy[chi_cy["crime_category"].isin(top8)]
    fig = px.area(chi_cy, x="year", y="pct_of_year", color="crime_category",
                  template=TEMPLATE,
                  color_discrete_map={k:CAT_COLORS.get(k,"#888") for k in top8},
                  labels={"pct_of_year":"% of All Crimes","year":"Year","crime_category":"Category"})
    fig.update_layout(height=420, legend=dict(x=1.01,y=1))
    st.plotly_chart(fig, use_container_width=True)

    # Arrest rate by category
    st.subheader("Arrest Rate by Crime Type")
    chi_arr = by_cat[(by_cat["city"]=="Chicago")&(by_cat["crime_category"]!="Other")].copy()
    chi_arr = chi_arr.dropna(subset=["arrest_rate"]).sort_values("arrest_rate")
    fig = px.bar(chi_arr, x="arrest_rate", y="crime_category", orientation="h",
                 color="arrest_rate", color_continuous_scale="RdYlGn",
                 template=TEMPLATE, text="arrest_rate",
                 labels={"arrest_rate":"Arrest Rate (%)","crime_category":""})
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=520, showlegend=False, coloraxis_showscale=False,
                      xaxis=dict(showgrid=False))
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
#  TAB 3 — SEATTLE
# ══════════════════════════════════════════════════════════════════════
with tab3:

    map_col, stat_col = st.columns([3,1])

    with stat_col:
        st.markdown("### Seattle")
        st.metric("Total Crimes",  f"{int(sea_ov['total_crimes']):,}")
        st.metric("Period",        f"{int(sea_ov['year_min'])}–{int(sea_ov['year_max'])}")
        st.metric("Neighborhoods", int(sea_ov["neighborhood_count"]))
        st.metric("Population",    f"{SEA_POP:,}")
        st.metric("Crime Rate",    f"{sea_ov['crimes_per_100k']:,.0f} /100k")

    with map_col:
        st.subheader("Crime Count by Neighborhood")
        fig = px.choropleth_mapbox(
            sea_neigh,
            geojson=sea_geo,
            locations="neighborhood",
            featureidkey="properties.neighborhood",
            color="crime_count",
            color_continuous_scale="Teal",
            mapbox_style="carto-darkmatter",
            zoom=10.5,
            center={"lat":47.61,"lon":-122.33},
            opacity=0.8,
            hover_name="neighborhood",
            hover_data={"crime_count":True,"large_neighborhood":True,"top_category":True,"neighborhood":False},
            labels={"crime_count":"Total Crimes","large_neighborhood":"District","top_category":"Top Crime"},
            template=TEMPLATE,
        )
        fig.update_layout(height=520, margin=dict(r=0,t=0,l=0,b=0),
                          coloraxis_colorbar=dict(title="Crimes",tickfont=dict(color="#aaa")))
        st.plotly_chart(fig, use_container_width=True)

    # Neighborhood rankings
    st.subheader("Neighborhood Rankings")
    r1, r2 = st.columns(2)

    with r1:
        st.markdown("**Top 10 — Most Crimes**")
        top10 = sea_neigh.nlargest(10,"crime_count").sort_values("crime_count")
        fig = px.bar(top10, x="crime_count", y="neighborhood", orientation="h",
                     template=TEMPLATE, color_discrete_sequence=[SEA_COLOR],
                     text="crime_count",
                     labels={"crime_count":"Total Crimes","neighborhood":""})
        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig.update_layout(height=380, showlegend=False, xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

    with r2:
        st.markdown("**Bottom 10 — Safest Neighborhoods**")
        bot10 = sea_neigh.nsmallest(10,"crime_count").sort_values("crime_count",ascending=False)
        fig = px.bar(bot10, x="crime_count", y="neighborhood", orientation="h",
                     template=TEMPLATE, color_discrete_sequence=["#2ECC71"],
                     text="crime_count",
                     labels={"crime_count":"Total Crimes","neighborhood":""})
        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig.update_layout(height=380, showlegend=False, xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

    # Seattle trend
    st.subheader("Seattle Crime Trend")
    sea_yr = by_year[by_year["city"]=="Seattle"]
    fig = px.area(sea_yr, x="year", y="crime_count",
                  template=TEMPLATE, color_discrete_sequence=[SEA_COLOR],
                  labels={"crime_count":"Total Crimes","year":"Year"})
    fig.add_vline(x=2020, line_dash="dash", line_color="rgba(255,255,255,0.25)",
                  annotation_text="COVID-19", annotation_font_color="#aaa",
                  annotation_position="top right")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Category mix
    st.subheader("How Has the Crime Mix Changed?")
    sea_cy = cat_year[cat_year["city"]=="Seattle"]
    top8s = sea_cy.groupby("crime_category")["crime_count"].sum().nlargest(8).index
    sea_cy = sea_cy[sea_cy["crime_category"].isin(top8s)]
    fig = px.area(sea_cy, x="year", y="pct_of_year", color="crime_category",
                  template=TEMPLATE,
                  color_discrete_map={k:CAT_COLORS.get(k,"#888") for k in top8s},
                  labels={"pct_of_year":"% of All Crimes","year":"Year","crime_category":"Category"})
    fig.update_layout(height=420, legend=dict(x=1.01,y=1))
    st.plotly_chart(fig, use_container_width=True)

    # Shootings
    if len(shootings) > 0:
        st.subheader("Shooting Incidents by Year")
        shoot_yr = shootings.groupby("year")["crime_count"].sum().reset_index()
        fig = px.bar(shoot_yr, x="year", y="crime_count",
                     template=TEMPLATE, color_discrete_sequence=[CHI_COLOR],
                     labels={"crime_count":"Shooting Incidents","year":"Year"},
                     text="crime_count")
        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig.add_vline(x=2020, line_dash="dash", line_color="rgba(255,255,255,0.25)",
                      annotation_text="COVID-19", annotation_font_color="#aaa")
        fig.update_layout(height=380, xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

        # Breakdown by shooting type
        shoot_type = shootings.groupby("shooting_type")["crime_count"].sum().reset_index()
        fig = px.pie(shoot_type, names="shooting_type", values="crime_count",
                     template=TEMPLATE, hole=0.45,
                     title="Shooting Incidents by Type",
                     color_discrete_sequence=px.colors.sequential.Teal)
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)
