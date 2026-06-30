// Package config loads service configuration from the environment.
package config

import "os"

type Config struct {
	GRPCAddr    string // address the gRPC data API listens on
	HTTPAddr    string // address the Gin ops server (health/metrics) listens on
	DatabaseURL string // postgres connection string for the prospects DB
}

func Load() Config {
	return Config{
		GRPCAddr:    getenv("GRPC_ADDR", ":50051"),
		HTTPAddr:    getenv("HTTP_ADDR", ":8080"),
		DatabaseURL: getenv("DATABASE_URL", "postgres://nhluser:nhlpassword@localhost:5432/prospects?sslmode=disable"),
	}
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
