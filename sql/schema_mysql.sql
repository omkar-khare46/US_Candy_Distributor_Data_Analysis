-- schema_mysql.sql
-- Star schema for the Candy Distributor data warehouse (MySQL version)
--
-- Differences from the SQLite version (sql/schema.sql):
--   - VARCHAR(n) instead of TEXT for primary/foreign key columns
--     (MySQL's InnoDB requires a defined key length for indexed columns)
--   - DATE is a real native type in MySQL, so order_date/ship_date are
--     stored as DATE, not TEXT — no ISO-string workaround needed
--   - ENGINE=InnoDB is specified explicitly (InnoDB supports foreign keys;
--     MySQL's older default engine, MyISAM, does not)
--   - FOREIGN_KEY_CHECKS is toggled off/on around the DROP/CREATE block,
--     since dropping tables in FK-dependency order matters otherwise

CREATE DATABASE IF NOT EXISTS candy_warehouse;
USE candy_warehouse;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_factories;
DROP TABLE IF EXISTS dim_targets;
DROP TABLE IF EXISTS dim_geography;

-- ---------------------------------------------------------------------------
-- Dimension: Factories
-- ---------------------------------------------------------------------------
CREATE TABLE dim_factories (
    factory_name   VARCHAR(100) PRIMARY KEY,
    latitude       DOUBLE,
    longitude      DOUBLE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Dimension: Targets (one row per division's sales target)
-- ---------------------------------------------------------------------------
CREATE TABLE dim_targets (
    division       VARCHAR(100) PRIMARY KEY,
    target         DOUBLE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Dimension: Products
-- ---------------------------------------------------------------------------
CREATE TABLE dim_products (
    product_id     VARCHAR(50) PRIMARY KEY,
    product_name   VARCHAR(200),
    division       VARCHAR(100),
    factory_name   VARCHAR(100),
    unit_price     DOUBLE,
    unit_cost      DOUBLE,
    FOREIGN KEY (division)     REFERENCES dim_targets(division),
    FOREIGN KEY (factory_name) REFERENCES dim_factories(factory_name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Dimension: Geography (trimmed us_zips — only zips present in Sales)
-- ---------------------------------------------------------------------------
CREATE TABLE dim_geography (
    zip                 VARCHAR(10) PRIMARY KEY,
    lat                 DOUBLE,
    lng                 DOUBLE,
    city                VARCHAR(100),
    state_id            VARCHAR(10),
    state_name          VARCHAR(100),
    zcta                VARCHAR(10),
    population          DOUBLE,
    density             DOUBLE,
    county_fips         VARCHAR(20),
    county_name         VARCHAR(100),
    county_weights      TEXT,
    county_names_all    VARCHAR(255),
    county_fips_all     VARCHAR(255),
    imprecise           VARCHAR(10),
    military            VARCHAR(10),
    timezone            VARCHAR(50)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Fact: Sales
-- Note: postal_code has no enforced FK to dim_geography, same reasoning as
-- the SQLite version — dim_geography is US-only, but Sales legitimately
-- includes non-US (Canadian) postal codes.
-- ---------------------------------------------------------------------------
CREATE TABLE fact_sales (
    row_id          INT PRIMARY KEY,
    order_id        VARCHAR(50),
    order_date      DATE,
    ship_date       DATE,
    ship_mode       VARCHAR(50),
    customer_id     VARCHAR(50),
    country_region  VARCHAR(50),
    city            VARCHAR(100),
    state_province  VARCHAR(100),
    postal_code     VARCHAR(10),
    division        VARCHAR(100),
    region          VARCHAR(50),
    product_id      VARCHAR(50),
    sales           DOUBLE,
    units            INT,
    gross_profit    DOUBLE,
    cost            DOUBLE,
    FOREIGN KEY (division)    REFERENCES dim_targets(division),
    FOREIGN KEY (product_id)  REFERENCES dim_products(product_id)
) ENGINE=InnoDB;

CREATE INDEX idx_fact_sales_product_id  ON fact_sales(product_id);
CREATE INDEX idx_fact_sales_postal_code ON fact_sales(postal_code);
CREATE INDEX idx_fact_sales_division    ON fact_sales(division);
CREATE INDEX idx_fact_sales_order_date  ON fact_sales(order_date);

SET FOREIGN_KEY_CHECKS = 1;
