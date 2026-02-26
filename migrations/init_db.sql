-- Database initialization script for Camp Booking System
-- This script creates the database schema and initial data

-- Create services table
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    required_documents TEXT,
    active BOOLEAN DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    date DATE NOT NULL,
    time_slot TEXT NOT NULL,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    camp TEXT NOT NULL,
    status TEXT DEFAULT 'confirmed' NOT NULL,
    reference_number TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE RESTRICT
);

-- Create admin_users table
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(date);
CREATE INDEX IF NOT EXISTS idx_bookings_service ON bookings(service_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_slot ON bookings(date, time_slot);

-- Insert default services
INSERT OR IGNORE INTO services (name, description, required_documents, active) VALUES
('Получить путевку', 'Получение путевки в лагерь', '["Оригинал и копия свидетельства о рождении ребенка", "Распечатанная квитанция об оплате", "Оригинал паспорта родителя"]', 1),
('Возврат денежных средств', 'Возврат денежных средств за путевку', '["Оригинал путевки", "Паспорт родителя", "Реквизиты для возврата"]', 1),
('Возврат путевки', 'Возврат неиспользованной путевки', '["Оригинал путевки", "Паспорт родителя"]', 1);
