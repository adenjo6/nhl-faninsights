package season

import (
	"testing"
	"time"
)

func at(y int, m time.Month) time.Time {
	return time.Date(y, m, 15, 12, 0, 0, 0, time.UTC)
}

func TestCurrent(t *testing.T) {
	cases := []struct {
		now  time.Time
		want string
	}{
		{at(2026, time.July), "2025-26"},     // off-season still belongs to the finished season
		{at(2026, time.August), "2026-27"},   // flip on August 1
		{at(2026, time.December), "2026-27"}, // mid-season
		{at(2027, time.January), "2026-27"},  // calendar year rolls, season doesn't
		{at(2027, time.June), "2026-27"},     // playoffs/late season
	}
	for _, c := range cases {
		if got := Current(c.now); got != c.want {
			t.Errorf("Current(%s) = %q, want %q", c.now.Format("2006-01"), got, c.want)
		}
	}
}

func TestPrevious(t *testing.T) {
	cases := []struct {
		now  time.Time
		want string
	}{
		{at(2026, time.July), "2024-25"},
		{at(2026, time.August), "2025-26"}, // the fallback the API serves until 2026-27 has data
		{at(2027, time.January), "2025-26"},
	}
	for _, c := range cases {
		if got := Previous(c.now); got != c.want {
			t.Errorf("Previous(%s) = %q, want %q", c.now.Format("2006-01"), got, c.want)
		}
	}
}
