// Package migrate applies the embedded goose migrations to the prospects DB.
package migrate

import (
	"database/sql"
	"fmt"

	_ "github.com/jackc/pgx/v5/stdlib" // database/sql driver "pgx"
	"github.com/pressly/goose/v3"

	"github.com/adenjo6/nhl-faninsights/prospect-service/migrations"
)

// Run opens a short-lived database/sql connection (goose needs one) and applies
// all pending migrations. The app itself uses a pgx pool separately.
func Run(databaseURL string) error {
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
