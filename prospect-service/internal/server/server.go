// Package server implements the ProspectService gRPC API over the sqlc data layer.
package server

import (
	"context"
	"errors"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/db"
	prospectsv1 "github.com/adenjo6/nhl-faninsights/prospect-service/internal/gen/prospects/v1"
	"github.com/adenjo6/nhl-faninsights/prospect-service/internal/season"
)

// Server implements prospectsv1.ProspectServiceServer.
type Server struct {
	prospectsv1.UnimplementedProspectServiceServer
	q *db.Queries
}

func New(q *db.Queries) *Server { return &Server{q: q} }

func (s *Server) ListProspects(ctx context.Context, req *prospectsv1.ListProspectsRequest) (*prospectsv1.ListProspectsResponse, error) {
	arg := db.ListProspectsParams{Season: season.Current(time.Now())}
	if p := req.GetPosition(); p != "" {
		arg.Position = &p
	}
	if l := req.GetLeague(); l != "" {
		arg.League = &l
	}
	rows, err := s.q.ListProspects(ctx, arg)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "list prospects: %v", err)
	}
	out := make([]*prospectsv1.Prospect, 0, len(rows))
	for _, r := range rows {
		out = append(out, toProto(fromListRow(r)))
	}
	return &prospectsv1.ListProspectsResponse{Prospects: out}, nil
}

func (s *Server) GetProspect(ctx context.Context, req *prospectsv1.GetProspectRequest) (*prospectsv1.GetProspectResponse, error) {
	row, err := s.q.GetProspect(ctx, db.GetProspectParams{
		Season: season.Current(time.Now()),
		ID:     req.GetId(),
	})
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, status.Errorf(codes.NotFound, "prospect %d not found", req.GetId())
		}
		return nil, status.Errorf(codes.Internal, "get prospect: %v", err)
	}
	return &prospectsv1.GetProspectResponse{Prospect: toProto(fromGetRow(row))}, nil
}

// rowView is the common shape of both query rows so we have one mapper.
type rowView struct {
	ID                int64
	FullName          string
	Position          string
	League            string
	Source            string
	DraftYear         *int32
	DraftOverall      *int32
	EliteprospectsUrl *string
	TeamName          *string
	Season            *string
	GP, G, A, P, PM, PIM *int32
	Wins, Losses, OTL    *int32
	SO, Saves, Shots     *int32
	GAA, SvPct           pgtype.Numeric
	FetchedAt         pgtype.Timestamptz
}

func fromListRow(r db.ListProspectsRow) rowView {
	return rowView{
		ID: r.ID, FullName: r.FullName, Position: r.Position, League: r.League, Source: r.Source,
		DraftYear: r.DraftYear, DraftOverall: r.DraftOverall,
		EliteprospectsUrl: r.EliteprospectsUrl, TeamName: r.TeamName,
		Season: r.Season, GP: r.GamesPlayed, G: r.Goals, A: r.Assists, P: r.Points,
		PM: r.PlusMinus, PIM: r.Pim,
		Wins: r.Wins, Losses: r.Losses, OTL: r.OtLosses,
		SO: r.Shutouts, Saves: r.Saves, Shots: r.Shots,
		GAA: r.Gaa, SvPct: r.SvPct,
		FetchedAt: r.FetchedAt,
	}
}

func fromGetRow(r db.GetProspectRow) rowView {
	return rowView{
		ID: r.ID, FullName: r.FullName, Position: r.Position, League: r.League, Source: r.Source,
		DraftYear: r.DraftYear, DraftOverall: r.DraftOverall,
		EliteprospectsUrl: r.EliteprospectsUrl, TeamName: r.TeamName,
		Season: r.Season, GP: r.GamesPlayed, G: r.Goals, A: r.Assists, P: r.Points,
		PM: r.PlusMinus, PIM: r.Pim,
		Wins: r.Wins, Losses: r.Losses, OTL: r.OtLosses,
		SO: r.Shutouts, Saves: r.Saves, Shots: r.Shots,
		GAA: r.Gaa, SvPct: r.SvPct,
		FetchedAt: r.FetchedAt,
	}
}

func toProto(v rowView) *prospectsv1.Prospect {
	p := &prospectsv1.Prospect{
		Id:                v.ID,
		FullName:          v.FullName,
		Position:          v.Position,
		League:            v.League,
		DraftYear:         derefI32(v.DraftYear),
		DraftOverall:      derefI32(v.DraftOverall),
		TeamName:          derefStr(v.TeamName),
		EliteprospectsUrl: derefStr(v.EliteprospectsUrl),
		HasLiveStats:      v.Source == "HOCKEYTECH",
	}
	if v.Season != nil { // LEFT JOIN produced a stats row
		p.CurrentSeason = &prospectsv1.SeasonStats{
			Season:      *v.Season,
			GamesPlayed: derefI32(v.GP),
			Goals:       derefI32(v.G),
			Assists:     derefI32(v.A),
			Points:      derefI32(v.P),
			PlusMinus:   derefI32(v.PM),
			Pim:         derefI32(v.PIM),
			UpdatedAt:   tsToString(v.FetchedAt),
		}
		// A goalie row carries the goalie columns; wins is NOT NULL in every
		// goalie upsert, so its presence identifies the line type.
		if v.Wins != nil {
			p.CurrentSeason.Goalie = &prospectsv1.GoalieStats{
				Wins:     derefI32(v.Wins),
				Losses:   derefI32(v.Losses),
				OtLosses: derefI32(v.OTL),
				Shutouts: derefI32(v.SO),
				Saves:    derefI32(v.Saves),
				Shots:    derefI32(v.Shots),
				Gaa:      numericToF64(v.GAA),
				SvPct:    numericToF64(v.SvPct),
			}
		}
	}
	return p
}

func numericToF64(n pgtype.Numeric) float64 {
	if !n.Valid {
		return 0
	}
	f, err := n.Float64Value()
	if err != nil {
		return 0
	}
	return f.Float64
}

func derefI32(p *int32) int32 {
	if p == nil {
		return 0
	}
	return *p
}

func derefStr(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}

func tsToString(ts pgtype.Timestamptz) string {
	if !ts.Valid {
		return ""
	}
	return ts.Time.UTC().Format(time.RFC3339)
}
