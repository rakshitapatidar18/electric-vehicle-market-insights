# Electric Vehicle Market Dataset — Data Dictionary

This data dictionary documents all 38 attributes present in the cleaned unified Electric Vehicle dataset (`data/processed/electric_vehicles_cleaned.csv`).

| Attribute | Data Type | Units / Format | Description & Example | Valid Domain / Range |
|:---|:---|:---|:---|:---|
| `vehicle_id` | String | `EV######` | Unique alphanumeric vehicle identifier (Primary Key). Example: `EV455665` | Unique per record |
| `model_name` | String | Name | Model brand designation. Example: `Drift-268`, `Nova-782` | Text |
| `manufacturer` | String | Name | Automotive manufacturer name. Example: `AmpereMotors`, `VoltWorks` | 200 distinct manufacturers |
| `model_year` | Integer | Year (`YYYY`) | Model release manufacturing year | `2018` to `2026` |
| `manufacturing_country` | String | Country name | Country of primary assembly. Example: `Germany`, `Japan`, `USA` | 10+ countries |
| `market_region` | String | Region name | Target geographical sales territory. Example: `North America`, `Europe` | 7 regions |
| `category` | String | Vehicle class | Vehicle category. Example: `Compact SUV`, `Sedan`, `Electric Bus` | 15 categories |
| `battery_capacity_kwh` | Float | Kilowatt-hours (kWh) | Total usable battery pack capacity | `1.5` to `410.0` kWh |
| `battery_type` | String | Chemistry code | Cell chemical formulation (`NMC`, `LFP`, `NCA`, `Sodium-Ion`, `Solid-State`) | 5 distinct chemistries |
| `battery_cycle_life` | Float | Charge cycles | Rated number of full charge-discharge cycles before 80% capacity retention | `500` to `4,640` cycles |
| `battery_degradation_pct_5yr` | Float | Percentage (%) | Expected degradation after 5 years of typical fleet usage | `2.0%` to `36.9%` |
| `range_km` | Float | Kilometers (km) | Standardized single-charge driving range (WLTP/EPA equivalent) | `55.0` to `660.0` km |
| `efficiency_wh_per_km` | Float | Watt-hours per km (Wh/km) | Energy consumption rate (lower = more energy efficient) | `9.9` to `2,261.4` Wh/km |
| `motor_power_kw` | Float | Kilowatts (kW) | Peak combined motor output power | `1.5` to `750.0` kW |
| `torque_nm` | Float | Newton-meters (Nm) | Instantaneous peak electric torque | `20.0` to `4,000.0` Nm |
| `num_motors` | Integer | Count | Number of electric drive motors installed (Single, Dual, Tri-motor) | `1` to `3` |
| `drivetrain` | String | Drive type | Drive configuration: `FWD` (Front-Wheel), `RWD` (Rear-Wheel), `AWD` (All-Wheel) | `FWD`, `RWD`, `AWD` |
| `top_speed_kmph` | Float | km/h | Electronically regulated or maximum physical top speed | `40.0` to `330.0` km/h |
| `acceleration_0_100_sec` | Float | Seconds | Time required to accelerate from 0 to 100 km/h | `1.9` to `30.0` seconds |
| `max_dc_charging_kw` | Float | Kilowatts (kW) | Peak DC fast charging acceptance rate | `3.0` to `350.0` kW |
| `charging_dc_fast_time_min` | Float | Minutes | Time to charge 10% to 80% on rated high-power DC fast charger | `8.0` to `59.6` minutes |
| `charging_ac_time_hr` | Float | Hours | Time to full charge via Level 2 residential/workplace AC charging | `0.3` to `30.0` hours |
| `num_charging_ports` | Integer | Count | Physical charging ports available on the vehicle chassis | `1` or `2` |
| `num_seats` | Integer | Count | Seating passenger capacity (e.g. 1 for scooter, 5 for sedan, 65 for bus) | `1` to `65` seats |
| `weight_kg` | Float | Kilograms (kg) | Curb weight of the vehicle including battery mass | `215.7` to `4,696.2` kg |
| `cargo_capacity_liters` | Float | Liters | Available trunk/frunk luggage volume | `15.0` to `2,001.5` liters |
| `price_usd` | Float | USD ($) | Manufacturer's Suggested Retail Price (MSRP) in US Dollars | `$900.21` to `$409,995.49` |
| `insurance_cost_usd_yearly` | Float | USD ($/year) | Estimated annual insurance premium | `$40.00` to `$12,000.00` |
| `warranty_years` | Integer | Years | Factory vehicle powertrain and battery warranty duration | `2` to `8` years |
| `resale_value_pct_3yr` | Float | Percentage (%) | Retained residual value after 3 years of ownership | `15.0%` to `90.0%` |
| `safety_rating_stars` | Integer | Star rating (1-5) | NCAP / NHTSA equivalent collision safety rating | `1` to `5` stars |
| `autonomous_level` | Integer | SAE Level (0-5) | Autonomous driving capability level (SAE Level 0 to Level 5) | `0` to `5` |
| `infotainment_screen_inch` | Float | Inches | Diagonal screen size of dashboard center touchscreen display | `3.0` to `17.0` inches |
| `co2_saved_tons_per_year` | Float | Metric Tons/year | Estimated greenhouse gas offset compared to internal combustion equivalent | `0.95` to `13.30` tons/yr |
| `annual_sales_units` | Integer | Unit volume | Annual sales volume delivered worldwide | `9` to `1,066,612` units |
| `customer_rating` | Float | Rating (1.00 - 5.00) | Aggregated consumer satisfaction rating index | `1.52` to `5.00` |
| `recommended_use_case` | String | Target segment | Optimal practical deployment (e.g., `Family Daily Use`, `Urban Commute`) | 7 segment labels |
| `split_source` | String | Origin tag | Tracks original data source partition (`train` or `test`) for data lineage | `train`, `test` |
