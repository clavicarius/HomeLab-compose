-- Fresh-stack grants for the poly-php MariaDB service.
-- This file is executed only on first initialization of ./mysql_data.

CREATE USER IF NOT EXISTS 'lamp_dbuser'@'%' IDENTIFIED BY 'lamp_dbSecretPassword';
GRANT ALL PRIVILEGES ON lamp_db.* TO 'lamp_dbuser'@'%';

CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'root_Hard2Crack!Secret';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

FLUSH PRIVILEGES;
