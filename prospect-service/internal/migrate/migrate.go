// Package migrate ensures the prospects database exists and applies the
// embedded goose migrations to it.
package migrate

import (
	"database/sql"
	"fmt"
	"net/url"
	"strings"

	_ "github.com/jackc/pgx/v5/stdlib" // database/sql driver "pgx"
	"github.com/pressly/goose/v3"

	"github.com/adenjo6/nhl-faninsights/prospect-service/migrations"
)

// Run ensures the target database exists, then opens a short-lived
// database/sql connection (goose needs one) and applies all pending
// migrations. The app itself uses a pgx pool separately.
func Run(databaseURL string) error {
	if err := ensureDatabase(databaseURL); err != nil {
		return fmt.Errorf("ensure database: %w", err)
	}

	conn, err := sql.Open("pgx", databaseURL)
	if err != nil {
		return fmt.Errorf("open db for migrations: %w", err)
	}
	defer conn.Close()

	goose.SetBaseFS(migrations.FS)
	if err := goose.SetDialect("postgres"); err != nil {
		return err
	}
	if err := goose.Up(conn, "."); err != nil {
		return fmt.Errorf("goose up: %w", err)
	}
	return nil
}

// ensureDatabase creates the target database if it does not already exist.
//
// The service owns its own database, so it must not assume some external step
// (a fresh-volume init script, a human running createdb) created it first. We
// connect to the maintenance "postgres" database on the same server and issue
// CREATE DATABASE when the target is missing. This is idempotent and safe to
// run on every startup.
func ensureDatabase(databaseURL string) error {
	u, err := url.Parse(databaseURL)
	if err != nil {
		return fmt.Errorf("parse database url: %w", err)
	}
	target := strings.TrimPrefix(u.Path, "/")
	if target == "" {
		return fmt.Errorf("database url has no database name")
	}

	// Connect to the maintenance database (CREATE DATABASE can't run against
	// the database being created, nor inside a transaction).
	maint := *u
	maint.Path = "/postgres"
	conn, err := sql.Open("pgx", maint.String())
	if err != nil {
		return fmt.Errorf("open maintenance db: %w", err)
	}
	defer conn.Close()

	var exists bool
	if err := conn.QueryRow(
		"SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = $1)", target,
	).Scan(&exists); err != nil {
		return fmt.Errorf("check database exists: %w", err)
	}
	if exists {
		return nil
	}

	// The name comes from our own config, but quote it defensively — CREATE
	// DATABASE can't be parameterized, so the identifier is interpolated.
	if _, err := conn.Exec("CREATE DATABASE " + quoteIdentifier(target)); err != nil {
		return fmt.Errorf("create database %q: %w", target, err)
	}
	return nil
}

// quoteIdentifier wraps a Postgres identifier in double quotes, escaping any
// embedded quotes, so it is safe to interpolate into DDL.
func quoteIdentifier(name string) string {
	return `"` + strings.ReplaceAll(name, `"`, `""`) + `"`
}
