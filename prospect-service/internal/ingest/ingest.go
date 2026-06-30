// Package ingest refreshes prospect season stats from HockeyTech.
package ingest

import (
	"context"
	"log"
	"sync"
	"time"

	"golang.org/x/sync/errgroup"

	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/db"
	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/hockeytech"
	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/season"
)

type Ingester struct {
	q  *db.Queries
	ht *hockeytech.Client
}

func New(q *db.Queries, ht *hockeytech.Client) *Ingester {
	return &Ingester{q: q, ht: ht}
}

// RunOnce refreshes every active HockeyTech prospect's current-season line.
// It fetches one bulk scorers feed per league concurrently (errgroup), then
// upserts the matching prospects. A single league's failure is logged and
// skipped rather than failing the whole run, so the next cron tick retries.
func (i *Ingester) RunOnce(ctx context.Context) error {
	rows, err := i.q.ListIngestableProspects(ctx)
	if err != nil {
		return err
	}

	// group prospects by league (client_code)
	byLeague := make(map[string][]db.ListIngestableProspectsRow)
	for _, r := range rows {
		if r.HockeytechClientCode == nil || r.HockeytechPlayerID == nil {
			continue
		}
		cc := *r.HockeytechClientCode
		byLeague[cc] = append(byLeague[cc], r)
	}

	seasonLabel := season.Current(time.Now())
	var mu sync.Mutex
	updated := 0

	g, gctx := errgroup.WithContext(ctx)
	g.SetLimit(4) // at most 4 leagues fetched concurrently
	for cc, players := range byLeague {
		cc, players := cc, players
		g.Go(func() error {
			lines, err := i.ht.FetchLeagueSeason(gctx, cc, seasonLabel)
			if err != nil {
				log.Printf("ingest: league %s fetch failed: %v", cc, err)
				return nil // isolate league failures
			}
			for _, p := range players {
				line, ok := lines[*p.HockeytechPlayerID]
				if !ok {
					log.Printf("ingest: %s (%s/%s) not found in feed", p.FullName, cc, *p.HockeytechPlayerID)
					continue
				}
				team := line.TeamName
				if err := i.q.UpsertSeasonStats(gctx, db.UpsertSeasonStatsParams{
					ProspectID:  p.ID,
					Season:      seasonLabel,
					TeamName:    &team,
					GamesPlayed: int32(line.GamesPlayed),
					Goals:       int32(line.Goals),
					Assists:     int32(line.Assists),
					Points:      int32(line.Points),
					PlusMinus:   int32(line.PlusMinus),
					Pim:         int32(line.PIM),
				}); err != nil {
					log.Printf("ingest: upsert %s failed: %v", p.FullName, err)
					continue
				}
				mu.Lock()
				updated++
				mu.Unlock()
			}
			return nil
		})
	}
	if err := g.Wait(); err != nil {
		return err
	}
	log.Printf("ingest: updated %d prospect stat line(s) for season %s", updated, seasonLabel)
	return nil
}
