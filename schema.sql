-- Schema only. Create a dedicated MySQL user and configure .env separately.
CREATE DATABASE IF NOT EXISTS locker_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE locker_db;
CREATE TABLE IF NOT EXISTS users (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(50) NOT NULL,
  phone VARCHAR(20),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS lockers (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  locker_number INT NOT NULL UNIQUE,
  status VARCHAR(20) NOT NULL DEFAULT 'available',
  user_id BIGINT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS locker_logs (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  locker_id BIGINT NOT NULL,
  user_id BIGINT NULL,
  action VARCHAR(20) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (locker_id) REFERENCES lockers(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;
INSERT IGNORE INTO lockers (locker_number, status) VALUES (1, 'available'), (2, 'available');
