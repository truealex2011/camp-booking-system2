-- Migration: Add display_order to services and create notification tables
-- Date: 2024
-- Description: Adds display_order field to services table and creates push_subscriptions and notifications tables

-- Add display_order column to services table
ALTER TABLE services ADD COLUMN display_order INTEGER DEFAULT 999;

-- Update display_order for priority services
UPDATE services SET display_order = 1 WHERE name = 'Получить путевку';
UPDATE services SET display_order = 2 WHERE name = 'Возврат денежных средств';
UPDATE services SET display_order = 2 WHERE name = 'Возврат дс';
UPDATE services SET display_order = 3 WHERE name = 'Возврат путевки';

-- Create push_subscriptions table
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL UNIQUE,
    endpoint TEXT NOT NULL,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- Create indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_booking ON notifications(booking_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);
