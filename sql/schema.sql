PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    login TEXT NOT NULL UNIQUE CHECK (length(trim(login)) > 0),
    password TEXT NOT NULL CHECK (length(password) > 0)
);

CREATE TABLE IF NOT EXISTS conditions (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0)
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    device_type TEXT NOT NULL CHECK (length(trim(device_type)) > 0),
    manufacturer TEXT NOT NULL CHECK (length(trim(manufacturer)) > 0),
    model TEXT NOT NULL CHECK (length(trim(model)) > 0),
    purchase_year INTEGER NOT NULL CHECK (purchase_year BETWEEN 1900 AND 9999),
    price REAL NOT NULL CHECK (price >= 0),
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE RESTRICT,
    condition_id INTEGER NOT NULL REFERENCES conditions(id) ON DELETE RESTRICT,
    service_interval INTEGER NOT NULL DEFAULT 3 CHECK (service_interval > 0)
);

CREATE INDEX IF NOT EXISTS devices_room_idx ON devices(room_id);
CREATE INDEX IF NOT EXISTS devices_condition_idx ON devices(condition_id);
