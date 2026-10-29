-- ==============================================================================
-- Analytical SQL Queries: Electric Vehicle Market Performance & Insights
-- Database: ev_market.db
-- Author: AI & Data Science Student
-- Description: High-performance analytical queries for KPI, manufacturer, 
--              category, battery, sales, and geographical market analysis.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- QUERY 1: KPI Summary Overview
-- Returns overall high-level executive metrics for dashboard header cards
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(v.vehicle_id) AS total_vehicles,
    COUNT(DISTINCT v.manufacturer_id) AS total_manufacturers,
    COUNT(DISTINCT v.category_id) AS total_categories,
    COUNT(DISTINCT v.manufacturing_country) AS total_manufacturing_countries,
    ROUND(AVG(v.range_km), 1) AS avg_driving_range_km,
    ROUND(MAX(v.range_km), 1) AS max_driving_range_km,
    ROUND(AVG(v.battery_capacity_kwh), 1) AS avg_battery_capacity_kwh,
    ROUND(AVG(v.price_usd), 2) AS avg_price_usd,
    SUM(v.annual_sales_units) AS total_annual_sales_units,
    ROUND(SUM(v.estimated_revenue_usd) / 1000000000.0, 2) AS total_revenue_billion_usd,
    ROUND(AVG(v.customer_rating), 2) AS avg_customer_rating
FROM vehicles v;


-- ------------------------------------------------------------------------------
-- QUERY 2: Top 10 Manufacturers by Total Sales Volume and Market Share
-- Evaluates manufacturer competitiveness and market concentration
-- ------------------------------------------------------------------------------
WITH global_fleet AS (
    SELECT SUM(annual_sales_units) AS global_sales_units FROM vehicles
)
SELECT 
    m.manufacturer_name,
    COUNT(v.vehicle_id) AS total_models_offered,
    SUM(v.annual_sales_units) AS total_sales_units,
    ROUND(SUM(v.estimated_revenue_usd) / 1000000.0, 2) AS revenue_million_usd,
    ROUND(AVG(v.price_usd), 2) AS avg_vehicle_price,
    ROUND(AVG(v.range_km), 1) AS avg_range_km,
    ROUND(AVG(v.customer_rating), 2) AS avg_rating,
    ROUND((CAST(SUM(v.annual_sales_units) AS REAL) / (SELECT global_sales_units FROM global_fleet)) * 100.0, 2) AS market_share_pct
FROM vehicles v
JOIN manufacturers m ON v.manufacturer_id = m.manufacturer_id
GROUP BY m.manufacturer_id, m.manufacturer_name
ORDER BY total_sales_units DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 3: Vehicle Category Comparison
-- Analyzes price, range, battery capacity, efficiency, and sales by category
-- ------------------------------------------------------------------------------
SELECT 
    c.category_name,
    COUNT(v.vehicle_id) AS vehicle_count,
    ROUND(AVG(v.price_usd), 2) AS avg_price_usd,
    ROUND(MIN(v.price_usd), 2) AS min_price_usd,
    ROUND(MAX(v.price_usd), 2) AS max_price_usd,
    ROUND(AVG(v.range_km), 1) AS avg_range_km,
    ROUND(AVG(v.battery_capacity_kwh), 1) AS avg_battery_kwh,
    ROUND(AVG(v.efficiency_wh_per_km), 1) AS avg_efficiency_wh_km,
    ROUND(AVG(v.acceleration_0_100_sec), 2) AS avg_0_100_sec,
    SUM(v.annual_sales_units) AS total_sales_units,
    ROUND(AVG(v.customer_rating), 2) AS avg_customer_rating
FROM vehicles v
JOIN categories c ON v.category_id = c.category_id
GROUP BY c.category_id, c.category_name
ORDER BY total_sales_units DESC;


-- ------------------------------------------------------------------------------
-- QUERY 4: Battery Technology & Chemistry Performance
-- Compares LFP, NMC, NCA, Sodium-Ion, and Solid-State adoption, degradation, & cycle life
-- ------------------------------------------------------------------------------
SELECT 
    b.battery_type_name AS battery_chemistry,
    COUNT(v.vehicle_id) AS total_models_deployed,
    ROUND(AVG(v.battery_capacity_kwh), 1) AS avg_capacity_kwh,
    ROUND(AVG(v.range_km), 1) AS avg_range_km,
    ROUND(AVG(v.battery_cycle_life), 0) AS avg_cycle_life_cycles,
    ROUND(AVG(v.battery_degradation_pct_5yr), 2) AS avg_5yr_degradation_pct,
    ROUND(AVG(v.charging_dc_fast_time_min), 1) AS avg_fast_charge_min,
    ROUND(AVG(v.price_usd / NULLIF(v.range_km, 0)), 2) AS avg_cost_per_km_range,
    SUM(v.annual_sales_units) AS total_sales_units
FROM vehicles v
JOIN battery_technologies b ON v.battery_type_id = b.battery_type_id
GROUP BY b.battery_type_id, b.battery_type_name
ORDER BY total_models_deployed DESC;


-- ------------------------------------------------------------------------------
-- QUERY 5: Annual Sales Trend and Fleet Evolution (2018 - 2026)
-- Evaluates industry growth, average prices, and technological progression over time
-- ------------------------------------------------------------------------------
SELECT 
    v.model_year,
    COUNT(v.vehicle_id) AS models_introduced,
    SUM(s.annual_sales_units) AS total_units_sold,
    ROUND(SUM(s.estimated_revenue_usd) / 1000000000.0, 2) AS revenue_billion_usd,
    ROUND(AVG(v.price_usd), 2) AS avg_price_usd,
    ROUND(AVG(v.range_km), 1) AS avg_range_km,
    ROUND(AVG(v.battery_capacity_kwh), 1) AS avg_battery_kwh,
    ROUND(AVG(v.charging_dc_fast_time_min), 1) AS avg_fast_charge_time_min
FROM vehicles v
JOIN vehicle_sales s ON v.vehicle_id = s.vehicle_id
GROUP BY v.model_year
ORDER BY v.model_year ASC;


-- ------------------------------------------------------------------------------
-- QUERY 6: Country-Wise Manufacturing Hubs & Global Distribution
-- Identifies leading manufacturing hubs and output volumes
-- ------------------------------------------------------------------------------
SELECT 
    v.manufacturing_country,
    COUNT(DISTINCT v.manufacturer_id) AS active_manufacturers,
    COUNT(v.vehicle_id) AS vehicle_count,
    SUM(v.annual_sales_units) AS total_sales_produced,
    ROUND(AVG(v.price_usd), 2) AS avg_price_usd,
    ROUND(AVG(v.range_km), 1) AS avg_range_km,
    ROUND(AVG(v.customer_rating), 2) AS avg_customer_satisfaction
FROM vehicles v
GROUP BY v.manufacturing_country
ORDER BY total_sales_produced DESC;


-- ------------------------------------------------------------------------------
-- QUERY 7: Regional Market Demand vs Production
-- Cross-tabulates manufacturing country against destination market region
-- ------------------------------------------------------------------------------
SELECT 
    v.market_region,
    COUNT(v.vehicle_id) AS models_available,
    SUM(v.annual_sales_units) AS total_regional_sales,
    ROUND(AVG(v.price_usd), 2) AS avg_regional_price,
    ROUND(AVG(v.customer_rating), 2) AS avg_satisfaction_rating
FROM vehicles v
GROUP BY v.market_region
ORDER BY total_regional_sales DESC;


-- ------------------------------------------------------------------------------
-- QUERY 8: Driving Range Champions (Top 10 Longest Range Vehicles)
-- Demonstrates multi-table joins using the unified analytical view
-- ------------------------------------------------------------------------------
SELECT 
    vehicle_id,
    model_name,
    manufacturer,
    category,
    battery_type,
    range_km,
    battery_capacity_kwh,
    efficiency_wh_per_km,
    top_speed_kmph,
    price_usd,
    customer_rating
FROM v_vehicles_complete
ORDER BY range_km DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 9: Best Value EVs (Lowest Cost per KM of Range)
-- Identifies top affordable models offering the highest range per dollar spent
-- ------------------------------------------------------------------------------
SELECT 
    v.vehicle_id,
    v.model_name,
    m.manufacturer_name,
    c.category_name,
    v.price_usd,
    v.range_km,
    ROUND(v.price_usd / v.range_km, 2) AS cost_per_km_range,
    v.customer_rating
FROM vehicles v
JOIN manufacturers m ON v.manufacturer_id = m.manufacturer_id
JOIN categories c ON v.category_id = c.category_id
WHERE v.range_km >= 200 AND v.price_usd < 35000
ORDER BY cost_per_km_range ASC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 10: Customer Satisfaction vs Safety Rating Correlation
-- Uses customer_ratings table join to evaluate ratings and resale values
-- ------------------------------------------------------------------------------
SELECT 
    r.safety_rating_stars,
    COUNT(v.vehicle_id) AS vehicle_count,
    ROUND(AVG(r.customer_rating), 2) AS avg_customer_rating,
    ROUND(AVG(r.resale_value_pct_3yr), 2) AS avg_3yr_resale_pct,
    ROUND(AVG(v.price_usd), 2) AS avg_price_usd,
    SUM(v.annual_sales_units) AS total_sales_units
FROM vehicles v
JOIN customer_ratings r ON v.vehicle_id = r.vehicle_id
GROUP BY r.safety_rating_stars
ORDER BY r.safety_rating_stars DESC;
