// Command server runs the prospect-service: a gRPC data API (consumed by the
// FastAPI gateway), a Gin HTTP ops surface (health/metrics), and a daily cron
// that refreshes prospect stats from HockeyTech.
package main

import (
	"context"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/robfig/cron/v3"
	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	healthpb "google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/reflection"

	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/config"
	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/db"
	prospectsv1 "github.com/adenjo6/nhl-faninsights/prospect-service/internal/gen/prospects/v1"
	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/hockeytech"
	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/ingest"
	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/migrate"
	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/server"
)

func main() {
	cfg := config.Load()

	// 1. Apply DB migrations before anything touches the schema.
	if err := migrate.Run(cfg.DatabaseURL); err != nil {
		log.Fatalf("migrations failed: %v", err)
	}
	log.Println("migrations applied")

	// 2. Connect the pgx pool used by the app.
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	pool, err := pgxpool.New(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("connect db: %v", err)
	}
	defer pool.Close()
	queries := db.New(pool)

	// 3. Ingestion: run once on startup (so there's data immediately) and then
	//    daily at 6am PT.
	ingester := ingest.New(queries, hockeytech.NewClient())
	go func() {
		if err := ingester.RunOnce(ctx); err != nil {
			log.Printf("startup ingest error: %v", err)
		}
	}()
	loc, err := time.LoadLocation("America/Los_Angeles")
	if err != nil {
		log.Fatalf("load timezone: %v", err)
	}
	c := cron.New(cron.WithLocation(loc))
	if _, err := c.AddFunc("0 6 * * *", func() {
		if err := ingester.RunOnce(context.Background()); err != nil {
			log.Printf("scheduled ingest error: %v", err)
		}
	}); err != nil {
		log.Fatalf("schedule cron: %v", err)
	}
	c.Start()
	defer c.Stop()

	// 4. gRPC data API.
	grpcServer := grpc.NewServer()
	prospectsv1.RegisterProspectServiceServer(grpcServer, server.New(queries))
	healthSrv := health.NewServer()
	healthpb.RegisterHealthServer(grpcServer, healthSrv)
	reflection.Register(grpcServer) // lets grpcurl / clients introspect in dev
	lis, err := net.Listen("tcp", cfg.GRPCAddr)
	if err != nil {
		log.Fatalf("listen %s: %v", cfg.GRPCAddr, err)
	}
	go func() {
		log.Printf("gRPC listening on %s", cfg.GRPCAddr)
		if err := grpcServer.Serve(lis); err != nil {
			log.Printf("grpc serve stopped: %v", err)
		}
	}()

	// 5. Gin HTTP ops surface (health now; Prometheus /metrics later).
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())
	r.GET("/health", func(ctx *gin.Context) {
		if err := pool.Ping(ctx); err != nil {
			ctx.JSON(http.StatusServiceUnavailable, gin.H{"status": "db_unavailable"})
			return
		}
		ctx.JSON(http.StatusOK, gin.H{"status": "ok"})
	})
	httpSrv := &http.Server{Addr: cfg.HTTPAddr, Handler: r}
	go func() {
		log.Printf("HTTP (ops) listening on %s", cfg.HTTPAddr)
		if err := httpSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("http serve stopped: %v", err)
		}
	}()

	// 6. Graceful shutdown.
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	<-stop
	log.Println("shutting down...")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()
	httpSrv.Shutdown(shutdownCtx)
	grpcServer.GracefulStop()
}
