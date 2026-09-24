#!/bin/bash
set -e

create_user_and_db() {
    local db_user=$1
    local db_password=$2
    local db_name=$3

    if [ -n "$db_user" ]; then
        echo "Creating user and database for '$db_name'..."
        
        # Create user if it doesn't exist
        local user_exists=$(psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$db_user'")
        if [ "$user_exists" != "1" ]; then
            psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -c "CREATE USER \"$db_user\" WITH PASSWORD '$db_password';"
        fi

        # Create database if it doesn't exist
        local db_exists=$(psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$db_name'")
        if [ "$db_exists" != "1" ]; then
            psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -c "CREATE DATABASE \"$db_name\";"
        fi

        # Grant privileges
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -c "GRANT ALL PRIVILEGES ON DATABASE \"$db_name\" TO \"$db_user\";"
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -c "ALTER DATABASE \"$db_name\" OWNER TO \"$db_user\";"
    fi
}

create_user_and_db "$CORE_POSTGRES_USER" "$CORE_POSTGRES_PASSWORD" "gaathacore_core"
create_user_and_db "$SUITE_POSTGRES_USER" "$SUITE_POSTGRES_PASSWORD" "gaathasuite"
create_user_and_db "$POS_POSTGRES_USER" "$POS_POSTGRES_PASSWORD" "gaathapos"
create_user_and_db "$SENTIRA_POSTGRES_USER" "$SENTIRA_POSTGRES_PASSWORD" "sentira"
create_user_and_db "$POSTPILOT_POSTGRES_USER" "$POSTPILOT_POSTGRES_PASSWORD" "postpilot"
