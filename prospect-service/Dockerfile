# prospect-service container (used by docker compose for local dev).
# Multi-stage: build a static binary, then ship it on a minimal alpine.
# Goose migrations are embedded in the binary (see migrations/embed.go), so no
# .sql files need to be copied into the runtime image.

# Stage 1: build
FROM golang:1.25-alpine AS builder
WORKDIR /src

# Cache module downloads separately from source.
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -o /out/prospect-service ./cmd/server

# Stage 2: runtime
FROM alpine:3.20
# ca-certificates for outbound HTTPS (HockeyTech ingest); tzdata for the
# America/Los_Angeles cron schedule loaded at runtime.
RUN apk add --no-cache ca-certificates tzdata
COPY --from=builder /out/prospect-service /usr/local/bin/prospect-service

# gRPC data API + HTTP ops (health) ports.
EXPOSE 50051 8080
ENTRYPOINT ["/usr/local/bin/prospect-service"]
