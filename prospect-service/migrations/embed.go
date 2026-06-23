// Package migrations embeds the goose SQL migrations so the service can apply
// them on startup without shipping the .sql files alongside the binary.
package migrations

import "embed"

//go:embed *.sql
var FS embed.FS
