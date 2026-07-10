// Package ingest refreshes prospect season stats from HockeyTech.
package ingest

import (
	"context"
	"log"
	"sync"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
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
// Skaters match against the bulk topscorers feed, goalies against topgoalies;
// each league fetches only the feeds its prospects need, concurrently
// (errgroup). A single league's failure is logged and skipped rather than
// failing the whole run, so the next cron tick retries.
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
			var skaters, goalies []db.ListIngestableProspectsRow
			for _, p := range players {
				if p.Position == "G" {
					goalies = append(goalies, p)
				} else {
					skaters = append(skaters, p)
				}
			}
			n := i.ingestSkaters(gctx, cc, seasonLabel, skaters) +
				i.ingestGoalies(gctx, cc, seasonLabel, goalies)
			mu.Lock()
			updated += n
			mu.Unlock()
			return nil
		})
	}
	if err := g.Wait(); err != nil {
		return err
	}
	log.Printf("ingest: updated %d prospect stat line(s) for season %s", updated, seasonLabel)
	return nil
}

func (i *Ingester) ingestSkaters(ctx context.Context, cc, seasonLabel string, players []db.ListIngestableProspectsRow) int {
	if len(players) == 0 {
		return 0
	}
	lines, err := i.ht.FetchLeagueSeason(ctx, cc, seasonLabel)
	if err != nil {
		log.Printf("ingest: league %s skater fetch failed: %v", cc, err)
		return 0 // isolate league failures
	}
	updated := 0
	for _, p := range players {
		line, ok := lines[*p.HockeytechPlayerID]
		if !ok {
			log.Printf("ingest: %s (%s/%s) not found in skater feed", p.FullName, cc, *p.HockeytechPlayerID)
			continue
		}
		team := line.TeamName
		if err := i.q.UpsertSeasonStats(ctx, db.UpsertSeasonStatsParams{
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
		updated++
	}
	return updated
}

func (i *Ingester) ingestGoalies(ctx context.Context, cc, seasonLabel string, players []db.ListIngestableProspectsRow) int {
	if len(players) == 0 {
		return 0
	}
	lines, err := i.ht.FetchLeagueGoalies(ctx, cc, seasonLabel)
	if err != nil {
		log.Printf("ingest: league %s goalie fetch failed: %v", cc, err)
		return 0 // isolate league failures
	}
	updated := 0
	for _, p := range players {
		line, ok := lines[*p.HockeytechPlayerID]
		if !ok {
			log.Printf("ingest: %s (%s/%s) not found in goalie feed", p.FullName, cc, *p.HockeytechPlayerID)
			continue
		}
		team := line.TeamName
		wins, losses, otl := int32(line.Wins), int32(line.Losses), int32(line.OTLosses)
		so, saves, shots := int32(line.Shutouts), int32(line.Saves), int32(line.Shots)
		if err := i.q.UpsertGoalieSeasonStats(ctx, db.UpsertGoalieSeasonStatsParams{
			ProspectID:  p.ID,
			Season:      seasonLabel,
			TeamName:    &team,
			GamesPlayed: int32(line.GamesPlayed),
			Wins:        &wins,
			Losses:      &losses,
			OtLosses:    &otl,
			Shutouts:    &so,
			Saves:       &saves,
			Shots:       &shots,
			Gaa:         numericFromString(line.GAA),
			SvPct:       numericFromString(line.SvPct),
		}); err != nil {
			log.Printf("ingest: upsert %s failed: %v", p.FullName, err)
			continue
		}
		updated++
	}
	return updated
}

// numericFromString converts a feed decimal like "2.51" into a pgtype.Numeric.
// Empty or unparseable input yields the invalid (NULL) numeric rather than an
// error — a missing GAA shouldn't sink the whole stat line.
func numericFromString(s string) pgtype.Numeric {
	var n pgtype.Numeric
	if s == "" {
		return n
	}
	if err := n.Scan(s); err != nil {
		return pgtype.Numeric{}
	}
	return n
}
