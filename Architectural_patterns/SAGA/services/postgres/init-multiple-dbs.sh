#!/bin/sh
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-SQL
    CREATE DATABASE orders_db;
    CREATE DATABASE payments_db;
    CREATE DATABASE inventory_db;
    CREATE DATABASE shipping_db;
SQL