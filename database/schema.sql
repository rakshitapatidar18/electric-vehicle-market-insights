-- ==============================================================================
-- Schema: Electric Vehicle Market Database (ev_market.db)
-- Author: AI & Data Science Student
-- Description: Normalized Relational Schema with Constraints, Foreign Keys & Indexes
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------------------
-- 1. Manufacturers Dimension Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS manufacturers (
    manufacturer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_name TEXT UNIQUE NOT NULL COLLATE NOCASE
);

-- ------------------------------------------------------------------------------
-- 2. Vehicle Categories Dimension Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL COLLATE NOCASE
);

-- ------------------------------------------------------------------------------
-- 3. Battery Technologies Dimension Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS battery_technologies (
    battery_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    battery_type_name TEXT UNIQUE NOT NULL COLLATE NOCASE
);

-- ------------------------------------------------------------------------------
-- 4. Vehicles Core Specifications Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    manufacturer_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    battery_type_id INTEGER NOT NULL,
    model_year INTEGER NOT NULL CHECK (model_year >= 2000 AND model_year <= 2035),
    manufacturing_country TEXT NOT NULL,
    market_region TEXT NOT NULL,
    battery_capacity_kwh REAL NOT NULL CHECK (battery_capacity_kwh > 0),
    battery_cycle_life REAL,
    battery_degradation_pct_5yr REAL,
    range_km REAL NOT NULL CHECK (range_km > 0),
    efficiency_wh_per_km REAL,
    motor_power_kw REAL,
    torque_nm REAL,
    num_motors INTEGER DEFAULT 1,
    drivetrain TEXT,
    top_speed_kmph REAL,
    acceleration_0_100_sec REAL,
    max_dc_charging_kw REAL,
    charging_dc_fast_time_min REAL,
    charging_ac_time_hr REAL,
    num_charging_ports INTEGER DEFAULT 1,
    num_seats INTEGER,
    weight_kg REAL,
    cargo_capacity_liters REAL,
    price_usd REAL NOT NULL CHECK (price_usd > 0),
    insurance_cost_usd_yearly REAL,
    warranty_years INTEGER,
    autonomous_level INTEGER CHECK (autonomous_level BETWEEN 0 AND 5),
    infotainment_screen_inch REAL,
    co2_saved_tons_per_year REAL,
    annual_sales_units INTEGER NOT NULL CHECK (annual_sales_units >= 0),
    estimated_revenue_usd REAL NOT NULL CHECK (estimated_revenue_usd >= 0),
    customer_rating REAL NOT NULL CHECK (customer_rating BETWEEN 1.0 AND 5.0),
    safety_rating_stars INTEGER NOT NULL CHECK (safety_rating_stars BETWEEN 1 AND 5),
    resale_value_pct_3yr REAL,
    recommended_use_case TEXT,
    split_source TEXT NOT NULL CHECK (split_source IN ('train', 'test')),
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturers(manufacturer_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
    FOREIGN KEY (battery_type_id) REFERENCES battery_technologies(battery_type_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- 5. Vehicle Sales Performance Table (Dedicated Sales Tracking)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicle_sales (
    sales_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT UNIQUE NOT NULL,
    model_year INTEGER NOT NULL,
    annual_sales_units INTEGER NOT NULL CHECK (annual_sales_units >= 0),
    estimated_revenue_usd REAL NOT NULL CHECK (estimated_revenue_usd >= 0),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- 6. Customer Ratings & Sentiment Table (Dedicated Reviews Tracking)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer_ratings (
    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT UNIQUE NOT NULL,
    customer_rating REAL NOT NULL CHECK (customer_rating BETWEEN 1.0 AND 5.0),
    safety_rating_stars INTEGER NOT NULL CHECK (safety_rating_stars BETWEEN 1 AND 5),
    resale_value_pct_3yr REAL,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- 7. High-Performance Indexes for Query Acceleration
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_vehicles_mfg ON vehicles(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_cat ON vehicles(category_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_bat ON vehicles(battery_type_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_year ON vehicles(model_year);
CREATE INDEX IF NOT EXISTS idx_vehicles_country ON vehicles(manufacturing_country);
CREATE INDEX IF NOT EXISTS idx_vehicles_region ON vehicles(market_region);
CREATE INDEX IF NOT EXISTS idx_vehicles_price ON vehicles(price_usd);
CREATE INDEX IF NOT EXISTS idx_vehicles_range ON vehicles(range_km);
CREATE INDEX IF NOT EXISTS idx_vehicles_sales ON vehicles(annual_sales_units);
CREATE INDEX IF NOT EXISTS idx_vehicles_rating ON vehicles(customer_rating);
CREATE INDEX IF NOT EXISTS idx_sales_vid ON vehicle_sales(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_sales_units ON vehicle_sales(annual_sales_units);
CREATE INDEX IF NOT EXISTS idx_ratings_vid ON customer_ratings(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_ratings_score ON customer_ratings(customer_rating);

-- ------------------------------------------------------------------------------
-- 8. Unified Analytics View
-- Joins dimension and fact tables for simplified reporting, BI, and Flask queries
-- ------------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_vehicles_complete AS
SELECT 
    v.vehicle_id,
    v.model_name,
    m.manufacturer_name AS manufacturer,
    c.category_name AS category,
    b.battery_type_name AS battery_type,
    v.model_year,
    v.manufacturing_country,
    v.market_region,
    v.battery_capacity_kwh,
    v.battery_cycle_life,
    v.battery_degradation_pct_5yr,
    v.range_km,
    v.efficiency_wh_per_km,
    v.motor_power_kw,
    v.torque_nm,
    v.num_motors,
    v.drivetrain,
    v.top_speed_kmph,
    v.acceleration_0_100_sec,
    v.max_dc_charging_kw,
    v.charging_dc_fast_time_min,
    v.charging_ac_time_hr,
    v.num_charging_ports,
    v.num_seats,
    v.weight_kg,
    v.cargo_capacity_liters,
    v.price_usd,
    v.insurance_cost_usd_yearly,
    v.warranty_years,
    v.autonomous_level,
    v.infotainment_screen_inch,
    v.co2_saved_tons_per_year,
    v.recommended_use_case,
    v.split_source,
    v.annual_sales_units,
    v.estimated_revenue_usd,
    v.customer_rating,
    v.safety_rating_stars,
    v.resale_value_pct_3yr
FROM vehicles v
JOIN manufacturers m ON v.manufacturer_id = m.manufacturer_id
JOIN categories c ON v.category_id = c.category_id
JOIN battery_technologies b ON v.battery_type_id = b.battery_type_id;
