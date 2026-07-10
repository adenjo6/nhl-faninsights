// Package hockeytech is a client for the HockeyTech "modulekit" feed
// (lscluster.hockeytech.com) that powers the CHL, AHL, and other league sites.
//
// Design note: rather than hitting the per-player feed (which is slow and emits
// a malformed "Statview category error" prefix before its JSON), we pull the
// bulk top-scorers feed once per league/season and index it by player_id. One
// clean request covers an entire league's skaters.
package hockeytech

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

const baseURL = "https://lscluster.hockeytech.com/feed/index.php"

// Per-league HockeyTech API keys, visible in each league's own public site
// traffic. Each CHL league runs its own instance with a distinct key.
const (
	ohlKey   = "2976319eb44abe94"
	whlKey   = "41b145a848f4bd67"
	qmjhlKey = "f1aa699db3d81487" // client_code "lhjmq"
	ahlKey   = "ccb91f29d6744675"
)

// SeasonLine is a single skater's regular-season totals for one league/season.
type SeasonLine struct {
	PlayerID    string
	TeamName    string
	GamesPlayed int
	Goals       int
	Assists     int
	Points      int
	PlusMinus   int
	PIM         int
}

// GoalieLine is a single goalie's regular-season totals for one league/season.
// GAA and SvPct carry the feed's own computed values verbatim (e.g. "2.51",
// "0.919") — the league's math is authoritative for empty-net/shootout edge
// cases, so we don't rederive them.
type GoalieLine struct {
	PlayerID    string
	TeamName    string
	GamesPlayed int
	Wins        int
	Losses      int
	OTLosses    int
	Shutouts    int
	Saves       int
	Shots       int
	GAA         string
	SvPct       string
}

// Client talks to the HockeyTech feed. Keys are per client_code (league).
type Client struct {
	http *http.Client
	keys map[string]string
}

func NewClient() *Client {
	return &Client{
		http: &http.Client{Timeout: 20 * time.Second},
		keys: map[string]string{
			"ohl":   ohlKey,
			"whl":   whlKey,
			"lhjmq": qmjhlKey, // QMJHL
			"ahl":   ahlKey,
		},
	}
}

// FetchLeagueSeason returns every skater's line for the given league
// (client_code) and season label (e.g. "2025-26"), indexed by player_id.
func (c *Client) FetchLeagueSeason(ctx context.Context, clientCode, seasonLabel string) (map[string]SeasonLine, error) {
	key, ok := c.keys[clientCode]
	if !ok {
		return nil, fmt.Errorf("no API key configured for client_code %q", clientCode)
	}
	seasonID, err := c.resolveSeasonID(ctx, clientCode, key, seasonLabel)
	if err != nil {
		return nil, fmt.Errorf("resolve season %q for %s: %w", seasonLabel, clientCode, err)
	}
	return c.fetchTopScorers(ctx, clientCode, key, seasonID)
}

// FetchLeagueGoalies returns every goalie's line for the given league and
// season label, indexed by player_id. Same bulk-feed design as skaters: the
// topgoalies view covers a league's entire crease in one request.
func (c *Client) FetchLeagueGoalies(ctx context.Context, clientCode, seasonLabel string) (map[string]GoalieLine, error) {
	key, ok := c.keys[clientCode]
	if !ok {
		return nil, fmt.Errorf("no API key configured for client_code %q", clientCode)
	}
	seasonID, err := c.resolveSeasonID(ctx, clientCode, key, seasonLabel)
	if err != nil {
		return nil, fmt.Errorf("resolve season %q for %s: %w", seasonLabel, clientCode, err)
	}
	return c.fetchTopGoalies(ctx, clientCode, key, seasonID)
}

func (c *Client) resolveSeasonID(ctx context.Context, clientCode, key, seasonLabel string) (string, error) {
	var resp struct {
		SiteKit struct {
			Seasons []struct {
				SeasonID   string `json:"season_id"`
				SeasonName string `json:"season_name"`
			} `json:"Seasons"`
		} `json:"SiteKit"`
	}
	if err := c.get(ctx, clientCode, key, "seasons", nil, &resp); err != nil {
		return "", err
	}
	// League instances format season names inconsistently: "2025-26",
	// "2025 - 26", "2025-26 | Regular Season". Normalize whitespace before matching.
	want := normalize(seasonLabel)
	for _, s := range resp.SiteKit.Seasons {
		n := normalize(s.SeasonName)
		if strings.HasPrefix(n, want) && strings.Contains(n, "regularseason") {
			return s.SeasonID, nil
		}
	}
	return "", fmt.Errorf("no regular season matching %q", seasonLabel)
}

func (c *Client) fetchTopScorers(ctx context.Context, clientCode, key, seasonID string) (map[string]SeasonLine, error) {
	var resp struct {
		SiteKit struct {
			Statviewtype []struct {
				PlayerID string `json:"player_id"`
				TeamName string `json:"team_name"`
				GP       string `json:"games_played"`
				G        string `json:"goals"`
				A        string `json:"assists"`
				P        string `json:"points"`
				PM       string `json:"plus_minus"`
				PIM      string `json:"penalty_minutes"`
			} `json:"Statviewtype"`
		} `json:"SiteKit"`
	}
	params := url.Values{
		"type":      {"topscorers"},
		"season_id": {seasonID},
		"first":     {"0"},
		"limit":     {"2000"},
		"sort":      {"active"},
		"stat":      {"all"},
	}
	if err := c.get(ctx, clientCode, key, "statviewtype", params, &resp); err != nil {
		return nil, err
	}
	out := make(map[string]SeasonLine, len(resp.SiteKit.Statviewtype))
	for _, r := range resp.SiteKit.Statviewtype {
		out[r.PlayerID] = SeasonLine{
			PlayerID:    r.PlayerID,
			TeamName:    r.TeamName,
			GamesPlayed: atoi(r.GP),
			Goals:       atoi(r.G),
			Assists:     atoi(r.A),
			Points:      atoi(r.P),
			PlusMinus:   atoi(r.PM),
			PIM:         atoi(r.PIM),
		}
	}
	return out, nil
}

func (c *Client) fetchTopGoalies(ctx context.Context, clientCode, key, seasonID string) (map[string]GoalieLine, error) {
	var resp struct {
		SiteKit struct {
			Statviewtype []struct {
				PlayerID string `json:"player_id"`
				TeamName string `json:"team_name"`
				GP       string `json:"games_played"`
				W        string `json:"wins"`
				L        string `json:"losses"`
				OTL      string `json:"ot_losses"`
				SO       string `json:"shutouts"`
				Saves    string `json:"saves"`
				Shots    string `json:"shots"`
				GAA      string `json:"goals_against_average"`
				SvPct    string `json:"save_percentage"`
			} `json:"Statviewtype"`
		} `json:"SiteKit"`
	}
	params := url.Values{
		"type":      {"topgoalies"},
		"season_id": {seasonID},
		"first":     {"0"},
		"limit":     {"500"},
		"sort":      {"active"},
		"stat":      {"all"},
	}
	if err := c.get(ctx, clientCode, key, "statviewtype", params, &resp); err != nil {
		return nil, err
	}
	out := make(map[string]GoalieLine, len(resp.SiteKit.Statviewtype))
	for _, r := range resp.SiteKit.Statviewtype {
		out[r.PlayerID] = GoalieLine{
			PlayerID:    r.PlayerID,
			TeamName:    r.TeamName,
			GamesPlayed: atoi(r.GP),
			Wins:        atoi(r.W),
			Losses:      atoi(r.L),
			OTLosses:    atoi(r.OTL),
			Shutouts:    atoi(r.SO),
			Saves:       atoi(r.Saves),
			Shots:       atoi(r.Shots),
			GAA:         strings.TrimSpace(r.GAA),
			SvPct:       strings.TrimSpace(r.SvPct),
		}
	}
	return out, nil
}

func (c *Client) get(ctx context.Context, clientCode, key, view string, extra url.Values, dst any) error {
	q := url.Values{
		"feed":        {"modulekit"},
		"fmt":         {"json"},
		"lang":        {"en"},
		"key":         {key},
		"client_code": {clientCode},
		"view":        {view},
	}
	for k, vs := range extra {
		for _, v := range vs {
			q.Add(k, v)
		}
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, baseURL+"?"+q.Encode(), nil)
	if err != nil {
		return err
	}
	res, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		return fmt.Errorf("hockeytech %s: status %d", view, res.StatusCode)
	}
	body, err := io.ReadAll(res.Body)
	if err != nil {
		return err
	}
	return json.Unmarshal(body, dst)
}

func atoi(s string) int {
	n, _ := strconv.Atoi(strings.TrimSpace(s))
	return n
}

// normalize lowercases and strips all whitespace, so season names with
// inconsistent spacing/punctuation across leagues compare cleanly.
func normalize(s string) string {
	return strings.ToLower(strings.Join(strings.Fields(s), ""))
}
