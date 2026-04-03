-- Master init script — run this once on Railway MySQL
-- Order matters: base schema first, then extensions

-- 1. Base tables (users, expenses, predictions, user_preferences)
SOURCE schema.sql;

-- 2. Privacy settings columns on users
SOURCE user_privacy_settings.sql;

-- 3. Income table
SOURCE income_table.sql;

-- 4. Enhanced features (category_budgets, planned_expenses, saving_goals)
SOURCE enhanced_features.sql;

-- 5. Anomaly detection columns on expenses
SOURCE anomaly_detection.sql;
