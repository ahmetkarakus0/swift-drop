#!/bin/bash
# POSTGRES_MULTIPLE_DATABASES format: "db:user:password,db2:user2:password2"
# Idempotent: only creates missing roles/databases, existing data is untouched.
set -eo pipefail

if [ -z "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
  echo "POSTGRES_MULTIPLE_DATABASES is empty, nothing to do"
  exit 0
fi

IFS=',' read -ra entries <<< "$POSTGRES_MULTIPLE_DATABASES"
for entry in "${entries[@]}"; do
  IFS=':' read -r db user password <<< "$(echo "$entry" | xargs)"
  echo "Ensuring database '$db' owned by '$user'"
  psql -v ON_ERROR_STOP=1 -v db="$db" -v user="$user" -v password="$password" <<-'EOSQL'
		SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'user', :'password')
		WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'user') \gexec

		SELECT format('CREATE DATABASE %I OWNER %I', :'db', :'user')
		WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'db') \gexec

		REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
	EOSQL
done
