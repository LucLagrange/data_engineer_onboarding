-- Schema Initialization
CREATE TABLE IF NOT EXISTS weather_metrics (
    weather VARCHAR(50),
    description TEXT,
    temperature NUMERIC(5, 2),
    humidity INTEGER,
    observed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);