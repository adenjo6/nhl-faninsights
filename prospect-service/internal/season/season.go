// Package season derives the current hockey-season label.
package season

import (
	"fmt"
	"time"
)

// Current returns the season label (e.g. "2025-26") for the given time.
// Hockey seasons span ~September–June, so months before August belong to the
// season that started the previous calendar year.
//
// Note: from August until the first games are played, Current names a season
// with no stats yet. Readers that display stats should fall back to
// Previous when the Current season has no rows (see server.resolveSeason) so
// the board keeps showing final totals through the off-season.
func Current(now time.Time) string {
	y := now.Year()
	if int(now.Month()) >= 8 { // August onward → new season starting this year
		return fmt.Sprintf("%d-%02d", y, (y+1)%100)
	}
	return fmt.Sprintf("%d-%02d", y-1, y%100)
}

// Previous returns the season label immediately before Current(now).
func Previous(now time.Time) string {
	y := now.Year()
	if int(now.Month()) >= 8 {
		return fmt.Sprintf("%d-%02d", y-1, y%100)
	}
	return fmt.Sprintf("%d-%02d", y-2, (y-1)%100)
}
