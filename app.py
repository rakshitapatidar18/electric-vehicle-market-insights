"""
Flask Web Application: Electric Vehicle Market Performance & Insights.
Provides responsive dashboards, interactive Plotly visualizations,
SQLite-backed paginated data explorer, and Tableau integration.
"""

import sys
import json
import sqlite3
import math
from pathlib import Path
from flask import Flask, render_template, request, abort, jsonify
import plotly
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.analysis import EVMarketAnalytics

app = Flask(__name__)
app.config.from_object(config.Config)

# Initialize analytical engine at startup (caches aggregations for instant rendering)
print("Initializing EV Market Analytics Engine for Flask Web Application...")
analytics_engine = EVMarketAnalytics()
cached_kpis = analytics_engine.get_executive_kpis()
cached_mfg = analytics_engine.get_manufacturer_performance(top_n=50)
cached_cat = analytics_engine.get_category_comparison()
cached_bat = analytics_engine.get_battery_analysis()
cached_trends = analytics_engine.get_annual_sales_trends()
cached_country = analytics_engine.get_country_manufacturing()
cached_region = analytics_engine.get_regional_market_demand()
print("Flask Analytics Cache populated successfully!")


def get_db_connection() -> sqlite3.Connection:
    """Creates a lightweight connection for fast paginated queries."""
    conn = sqlite3.connect(str(config.DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def apply_plotly_dark_theme(fig: go.Figure, title: str = "") -> go.Figure:
    """Applies a consistent dark theme matching the application UI."""
    fig.update_layout(
        title=dict(text=title, font=dict(color="#f8fafc", size=14, family="-apple-system, BlinkMacSystemFont, Segoe UI")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", family="-apple-system, BlinkMacSystemFont, Segoe UI"),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor="rgba(51, 65, 85, 0.4)", zerolinecolor="rgba(51, 65, 85, 0.6)"),
        yaxis=dict(gridcolor="rgba(51, 65, 85, 0.4)", zerolinecolor="rgba(51, 65, 85, 0.6)"),
        hoverlabel=dict(bgcolor="#1e293b", font_size=12, font_family="-apple-system, BlinkMacSystemFont, Segoe UI")
    )
    return fig


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@app.route("/")
def index():
    """Home / Project Overview page."""
    return render_template("index.html", kpis=cached_kpis)


@app.route("/dashboard")
def dashboard():
    """Market Dashboard with interactive Plotly visual charts."""
    selected_category = request.args.get("category", "All")
    all_categories = sorted(cached_cat["category"].tolist())

    # 1. Category Sales & Price Chart
    cat_df = cached_cat.copy()
    if selected_category != "All":
        cat_df = cat_df[cat_df["category"] == selected_category]

    fig_cat = go.Figure()
    fig_cat.add_trace(go.Bar(
        x=cat_df["category"],
        y=cat_df["total_sales_units"],
        name="Sales Units",
        marker_color="#06b6d4"
    ))
    fig_cat.add_trace(go.Scatter(
        x=cat_df["category"],
        y=cat_df["avg_price_usd"],
        name="Avg Price ($)",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#f59e0b", width=2),
        marker=dict(size=7)
    ))
    fig_cat.update_layout(
        yaxis=dict(title="Sales Units", gridcolor="rgba(51, 65, 85, 0.4)"),
        yaxis2=dict(title="Avg Price ($ USD)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    apply_plotly_dark_theme(fig_cat)

    # 2. Regional Sales Distribution Pie Chart
    reg_df = cached_region.copy()
    fig_reg = px.pie(
        reg_df,
        names="market_region",
        values="total_regional_sales",
        hole=0.45,
        color_discrete_sequence=["#06b6d4", "#0284c7", "#10b981", "#f59e0b", "#a855f7", "#ec4899", "#64748b"]
    )
    fig_reg.update_traces(textposition="inside", textinfo="percent+label")
    apply_plotly_dark_theme(fig_reg)

    # 3. Driving Range vs Price Scatter
    fig_rp = px.scatter(
        cached_cat,
        x="avg_range_km",
        y="avg_price_usd",
        size="vehicle_count",
        color="category",
        hover_name="category",
        labels={"avg_range_km": "Avg Range (km)", "avg_price_usd": "Avg Price ($ USD)"}
    )
    apply_plotly_dark_theme(fig_rp)
    fig_rp.update_layout(showlegend=False)

    # 4. Annual Fleet Evolution Chart
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=cached_trends["model_year"],
        y=cached_trends["total_units_sold"] / 1e6,
        name="Annual Deliveries (M)",
        marker_color="#10b981"
    ))
    fig_trend.add_trace(go.Scatter(
        x=cached_trends["model_year"],
        y=cached_trends["avg_battery_kwh"],
        name="Avg Battery (kWh)",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#06b6d4", width=2)
    ))
    fig_trend.update_layout(
        yaxis=dict(title="Deliveries (Millions)", gridcolor="rgba(51, 65, 85, 0.4)"),
        yaxis2=dict(title="Avg Battery Pack (kWh)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    apply_plotly_dark_theme(fig_trend)

    return render_template(
        "dashboard.html",
        categories=all_categories,
        selected_category=selected_category,
        chart_category_json=json.dumps(fig_cat, cls=plotly.utils.PlotlyJSONEncoder),
        chart_region_json=json.dumps(fig_reg, cls=plotly.utils.PlotlyJSONEncoder),
        chart_range_price_json=json.dumps(fig_rp, cls=plotly.utils.PlotlyJSONEncoder),
        chart_trend_json=json.dumps(fig_trend, cls=plotly.utils.PlotlyJSONEncoder)
    )


@app.route("/manufacturers")
def manufacturers():
    """Manufacturer Competitiveness & Market Share page."""
    top_mfg = cached_mfg.head(15).copy()

    # 1. Top 15 Automakers Sales & Revenue Bar Chart
    fig_sales = go.Figure()
    fig_sales.add_trace(go.Bar(
        x=top_mfg["manufacturer"],
        y=top_mfg["total_sales_units"] / 1e6,
        name="Sales (M Units)",
        marker_color="#0284c7"
    ))
    fig_sales.update_layout(yaxis=dict(title="Sales Units (Millions)"))
    apply_plotly_dark_theme(fig_sales)

    # 2. Market Share Concentration Donut
    fig_share = px.pie(
        top_mfg,
        names="manufacturer",
        values="total_sales_units",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Dark24
    )
    fig_share.update_traces(textposition="inside", textinfo="percent+label")
    apply_plotly_dark_theme(fig_share)

    table_data = cached_mfg.to_dict(orient="records")

    return render_template(
        "manufacturers.html",
        manufacturers_table=table_data,
        chart_mfg_sales_json=json.dumps(fig_sales, cls=plotly.utils.PlotlyJSONEncoder),
        chart_mfg_share_json=json.dumps(fig_share, cls=plotly.utils.PlotlyJSONEncoder)
    )


@app.route("/batteries")
def batteries():
    """Battery Chemistry & Longevity analysis page."""
    bat_df = cached_bat.copy()

    # 1. Chemistry Share Donut
    fig_share = px.pie(
        bat_df,
        names="battery_type",
        values="total_models_deployed",
        hole=0.45,
        color="battery_type",
        color_discrete_map={
            "NMC": "#0284c7",
            "LFP": "#10b981",
            "NCA": "#f59e0b",
            "Sodium-Ion": "#a855f7",
            "Solid-State": "#ec4899"
        }
    )
    fig_share.update_traces(textposition="inside", textinfo="percent+label")
    apply_plotly_dark_theme(fig_share)

    # 2. Degradation vs Cycle Life Grouped Bar
    fig_deg = go.Figure()
    fig_deg.add_trace(go.Bar(
        x=bat_df["battery_type"],
        y=bat_df["avg_5yr_degradation_pct"],
        name="5-Yr Degradation (%)",
        marker_color="#f43f5e"
    ))
    fig_deg.add_trace(go.Scatter(
        x=bat_df["battery_type"],
        y=bat_df["avg_cycle_life_cycles"],
        name="Cycle Life (Cycles)",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#10b981", width=3),
        marker=dict(size=8)
    ))
    fig_deg.update_layout(
        yaxis=dict(title="5-Yr Degradation (%)", gridcolor="rgba(51, 65, 85, 0.4)"),
        yaxis2=dict(title="Rated Cycle Life (Cycles)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    apply_plotly_dark_theme(fig_deg)

    # 3. DC Fast Charging Duration
    fig_charge = px.bar(
        bat_df,
        x="battery_type",
        y="avg_fast_charge_min",
        color="battery_type",
        labels={"avg_fast_charge_min": "Time to 80% (min)", "battery_type": "Chemistry"},
        color_discrete_sequence=["#06b6d4", "#10b981", "#f59e0b", "#a855f7", "#ec4899"]
    )
    apply_plotly_dark_theme(fig_charge)
    fig_charge.update_layout(showlegend=False)

    # 4. Battery Cost per KM Range
    fig_cost = px.bar(
        bat_df,
        x="battery_type",
        y="avg_cost_per_km_range",
        color="battery_type",
        labels={"avg_cost_per_km_range": "Cost / km Range ($ USD)", "battery_type": "Chemistry"},
        color_discrete_sequence=["#0284c7", "#10b981", "#f59e0b", "#a855f7", "#ec4899"]
    )
    apply_plotly_dark_theme(fig_cost)
    fig_cost.update_layout(showlegend=False)

    return render_template(
        "batteries.html",
        battery_table=bat_df.to_dict(orient="records"),
        chart_battery_share_json=json.dumps(fig_share, cls=plotly.utils.PlotlyJSONEncoder),
        chart_battery_deg_json=json.dumps(fig_deg, cls=plotly.utils.PlotlyJSONEncoder),
        chart_battery_charge_json=json.dumps(fig_charge, cls=plotly.utils.PlotlyJSONEncoder),
        chart_battery_cost_json=json.dumps(fig_cost, cls=plotly.utils.PlotlyJSONEncoder)
    )


@app.route("/explorer")
def explorer():
    """Searchable and paginated vehicle data explorer powered by SQLite."""
    page = request.args.get("page", 1, type=int)
    per_page = 25
    offset = (page - 1) * per_page

    search_query = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "All")
    selected_battery = request.args.get("battery", "All")
    sort_by = request.args.get("sort_by", "range_km")
    sort_order = request.args.get("order", "DESC").upper()

    # Whitelist sorting to prevent SQL injection
    valid_sort_cols = ["range_km", "price_usd", "annual_sales_units", "customer_rating", "model_year", "vehicle_id"]
    if sort_by not in valid_sort_cols:
        sort_by = "range_km"
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "DESC"

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build dynamic query
    conditions = ["1=1"]
    params = []

    if search_query:
        conditions.append("(model_name LIKE ? OR manufacturer LIKE ?)")
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if selected_category != "All":
        conditions.append("category = ?")
        params.append(selected_category)

    if selected_battery != "All":
        conditions.append("battery_type = ?")
        params.append(selected_battery)

    where_clause = " AND ".join(conditions)

    # Count total matching rows
    count_sql = f"SELECT COUNT(*) FROM v_vehicles_complete WHERE {where_clause};"
    cursor.execute(count_sql, params)
    total_records = cursor.fetchone()[0]
    total_pages = max(1, math.ceil(total_records / per_page))

    # Fetch page slice
    data_sql = f"""
        SELECT vehicle_id, model_name, manufacturer, category, model_year,
               battery_type, battery_capacity_kwh, range_km, price_usd,
               annual_sales_units, customer_rating
        FROM v_vehicles_complete
        WHERE {where_clause}
        ORDER BY {sort_by} {sort_order}
        LIMIT ? OFFSET ?;
    """
    cursor.execute(data_sql, params + [per_page, offset])
    rows = cursor.fetchall()
    vehicles = [dict(r) for r in rows]
    conn.close()

    all_categories = sorted(cached_cat["category"].tolist())
    all_batteries = sorted(cached_bat["battery_type"].tolist())

    return render_template(
        "data_explorer.html",
        vehicles=vehicles,
        page=page,
        total_pages=total_pages,
        total_records=total_records,
        per_page=per_page,
        search_query=search_query,
        selected_category=selected_category,
        selected_battery=selected_battery,
        sort_by=sort_by,
        sort_order=sort_order,
        categories=all_categories,
        battery_types=all_batteries
    )


@app.route("/tableau")
def tableau_embed():
    """Integrated Plotly dashboard using pre‑exported Tableau CSV files.
    Replaces the previous Tableau embed guide.
    """
    # Load CSVs – handle missing files gracefully
    data_dir = Path(__file__).resolve().parent / "data" / "processed"
    try:
        df_master = pd.read_csv(data_dir / "ev_tableau_export.csv")
        df_mfg = pd.read_csv(data_dir / "tableau_manufacturer_kpis.csv")
        df_cat = pd.read_csv(data_dir / "tableau_category_kpis.csv")
        df_bat = pd.read_csv(data_dir / "tableau_battery_kpis.csv")
        df_year = pd.read_csv(data_dir / "tableau_yearly_trends.csv")
        df_country = pd.read_csv(data_dir / "tableau_country_kpis.csv")
    except Exception as e:
        # If any file is missing, show a simple error page
        abort(500, description=f"Unable to load Tableau CSV data: {e}")

    # ---------- Executive KPI cards (simple aggregates) ----------
    total_vehicles = len(df_master)
    total_sales_units = df_master["annual_sales_units"].sum()
    avg_price = df_master["price_usd"].mean()
    avg_range = df_master["range_km"].mean()
    kpi_cards = {
        "Total Vehicles": f"{total_vehicles:,}",
        "Total Sales Units": f"{int(total_sales_units):,}",
        "Avg Price (USD)": f"${avg_price:,.0f}",
        "Avg Range (km)": f"{avg_range:.1f} km",
    }

    # ---------- Manufacturer comparison bar ----------
    fig_mfg = go.Figure()
    fig_mfg.add_trace(go.Bar(
        x=df_mfg["manufacturer"],
        y=df_mfg["total_sales_units"] / 1e6,
        marker_color="#0284c7",
        name="Sales (M units)"
    ))
    fig_mfg.update_layout(
        yaxis=dict(title="Sales (Millions)"),
        xaxis=dict(tickangle=-45),
        title="Top Manufacturers – Sales Volume"
    )
    apply_plotly_dark_theme(fig_mfg)

    # ---------- Category comparison ----------
    fig_cat = go.Figure()
    fig_cat.add_trace(go.Bar(
        x=df_cat["category"],
        y=df_cat["total_sales_units"] / 1e6,
        marker_color="#06b6d4",
        name="Sales (M)"
    ))
    fig_cat.update_layout(
        yaxis=dict(title="Sales (Millions)"),
        xaxis=dict(tickangle=-45),
        title="Vehicle Category – Sales Volume"
    )
    apply_plotly_dark_theme(fig_cat)

    # ---------- Battery technology insights ----------
    fig_bat = go.Figure()
    fig_bat.add_trace(go.Bar(
        x=df_bat["battery_type"],
        y=df_bat["total_sales_units"] / 1e6,
        marker_color="#10b981",
        name="Sales (M)"
    ))
    fig_bat.update_layout(
        yaxis=dict(title="Sales (Millions)"),
        xaxis=dict(tickangle=-45),
        title="Battery Chemistry – Sales Volume"
    )
    apply_plotly_dark_theme(fig_bat)

    # ---------- Yearly trends line chart ----------
    fig_year = go.Figure()
    fig_year.add_trace(go.Scatter(
        x=df_year["model_year"],
        y=df_year["total_units_sold"] / 1e6,
        mode="lines+markers",
        name="Units Sold (M)",
        line=dict(color="#f59e0b")
    ))
    fig_year.add_trace(go.Scatter(
        x=df_year["model_year"],
        y=df_year["avg_price_usd"],
        mode="lines+markers",
        name="Avg Price ($)",
        yaxis="y2",
        line=dict(color="#06b6d4")
    ))
    fig_year.update_layout(
        yaxis=dict(title="Units Sold (M)"),
        yaxis2=dict(title="Avg Price ($)", overlaying="y", side="right", showgrid=False),
        xaxis=dict(title="Model Year"),
        title="Yearly Market Trends"
    )
    apply_plotly_dark_theme(fig_year)

    # ---------- Country comparison ----------
    fig_country = go.Figure()
    fig_country.add_trace(go.Bar(
        x=df_country["manufacturing_country"],
        y=df_country["total_sales_produced"] / 1e6,
        marker_color="#a855f7",
        name="Sales (M)"
    ))
    fig_country.update_layout(
        yaxis=dict(title="Sales (Millions)"),
        xaxis=dict(tickangle=-45),
        title="Country‑wise Production & Sales"
    )
    apply_plotly_dark_theme(fig_country)

    return render_template(
        "tableau_dashboard.html",
        kpi_cards=kpi_cards,
        chart_mfg_json=json.dumps(fig_mfg, cls=plotly.utils.PlotlyJSONEncoder),
        chart_cat_json=json.dumps(fig_cat, cls=plotly.utils.PlotlyJSONEncoder),
        chart_bat_json=json.dumps(fig_bat, cls=plotly.utils.PlotlyJSONEncoder),
        chart_year_json=json.dumps(fig_year, cls=plotly.utils.PlotlyJSONEncoder),
        chart_country_json=json.dumps(fig_country, cls=plotly.utils.PlotlyJSONEncoder),
    )
    """Integrated Plotly dashboard using pre‑exported Tableau CSV files.
    Replaces the previous Tableau embed guide.
    """
    # Load CSVs – handle missing files gracefully
    data_dir = Path(__file__).resolve().parent / "data" / "processed"
    try:
        df_master = pd.read_csv(data_dir / "ev_tableau_export.csv")
        df_mfg = pd.read_csv(data_dir / "tableau_manufacturer_kpis.csv")
        df_cat = pd.read_csv(data_dir / "tableau_category_kpis.csv")
        df_bat = pd.read_csv(data_dir / "tableau_battery_kpis.csv")
        df_year = pd.read_csv(data_dir / "tableau_yearly_trends.csv")
        df_country = pd.read_csv(data_dir / "tableau_country_kpis.csv")
    except Exception as e:
        # If any file is missing, show a simple error page
        abort(500, description=f"Unable to load Tableau CSV data: {e}")

    # ---------- Executive KPI cards (simple aggregates) ----------
    total_vehicles = len(df_master)
    total_sales_units = df_master["annual_sales_units"].sum()
    avg_price = df_master["price_usd"].mean()
    avg_range = df_master["range_km"].mean()
    kpi_cards = {
        "Total Vehicles": f"{total_vehicles:,}",
        "Total Sales Units": f"{int(total_sales_units):,}",
        "Avg Price (USD)": f"${avg_price:,.0f}",
        "Avg Range (km)": f"{avg_range:.1f} km",
    }

    # ---------- Manufacturer comparison bar ----------
    fig_mfg = go.Figure()
    fig_mfg.add_trace(go.Bar(
        x=df_mfg["manufacturer"],
        y=df_mfg["total_sales_units"] / 1e6,  # show in millions
        marker_color="#0284c7",
        name="Sales (M units)"
    ))
    fig_mfg.update_layout(
        yaxis=dict(title="Sales (Millions)"),
        xaxis=dict(tickangle=-45),
        title="Top Manufacturers – Sales Volume"
    )
    apply_plotly_dark_theme(fig_mfg)

    # ---------- Category comparison ----------
    fig_cat = go.Figure()
    fig_cat.add_trace(go.Bar(
        x=df_cat["category"],
        y=df_cat["total_sales_units"] / 1e6,
        marker_color="#06b6d4",
        name="Sales (M)"
    ))
    fig_cat.update_layout(
        yaxis=dict(title="Sales (Millions)"),
        xaxis=dict(tickangle=-45),
        title="Vehicle Category – Sales Volume"
    )
    apply_plotly_dark_theme(fig_cat)

    # ---------- Battery technology insights ----------
    fig_bat = go.Figure()
    fig_bat.add_trace(go.Bar(
        x=df_bat["battery_type"],
        y=df_bat["total_sales_units"] / 1e6,
        marker_color="#10b981",
        name="Sales (M)"
    ))
    fig_bat.update_layout(
        yaxis=dict(title="Sales (Millions)"),
        xaxis=dict(tickangle=-45),
        title="Battery Chemistry – Sales Volume"
    )
    apply_plotly_dark_theme(fig_bat)

    # ---------- Yearly trends line chart ----------
    fig_year = go.Figure()
    fig_year.add_trace(go.Scatter(
        x=df_year["model_year"],
        y=df_year["total_units_sold"] / 1e6,
        mode="lines+markers",
        name="Units Sold (M)",
        line=dict(color="#f59e0b")
    ))
    fig_year.add_trace(go.Scatter(
        x=df_year["model_year"],
        y=df_year["avg_price_usd"],
        mode="lines+markers",
        name="Avg Price ($)",
        yaxis="y2",
        line=dict(color="#06b6d4")
    ))
    fig_year.update_layout(
        yaxis=dict(title="Units Sold (M)"),
        yaxis2=dict(title="Avg Price ($)", overlaying="y", side="right", showgrid=False),
        xaxis=dict(title="Model Year"),
        title="Yearly Market Trends"
    )
    apply_plotly_dark_theme(fig_year)

    # ---------- Country comparison ----------
    fig_country = go.Figure()
    fig_country.add_trace(go.Bar(
        x=df_country["manufacturing_country"],
        y=df_country["total_sales_produced"] / 1e6,
        marker_color="#a855f7",
        name="Sales (M)"
    ))
    fig_country.update_layout(
        yaxis=dict(title="Sales (Millions)"),
        xaxis=dict(tickangle=-45),
        title="Country‑wise Production & Sales"
    )
    apply_plotly_dark_theme(fig_country)

    return render_template(
        "tableau_dashboard.html",
        kpi_cards=kpi_cards,
        chart_mfg_json=json.dumps(fig_mfg, cls=plotly.utils.PlotlyJSONEncoder),
        chart_cat_json=json.dumps(fig_cat, cls=plotly.utils.PlotlyJSONEncoder),
        chart_bat_json=json.dumps(fig_bat, cls=plotly.utils.PlotlyJSONEncoder),
        chart_year_json=json.dumps(fig_year, cls=plotly.utils.PlotlyJSONEncoder),
        chart_country_json=json.dumps(fig_country, cls=plotly.utils.PlotlyJSONEncoder),
    )

    """Tableau BI Dashboard Embed / Fallback Guidance page."""
    tableau_url = app.config.get("TABLEAU_EMBED_URL", "").strip()
    return render_template("tableau_embed.html", tableau_url=tableau_url)


@app.route("/about")
def about():
    """About & Academic Methodology page."""
    return render_template("about.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("about.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("about.html"), 500


if __name__ == "__main__":
    print(f"Starting EV Market Insights Web App on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=config.Config.DEBUG)
