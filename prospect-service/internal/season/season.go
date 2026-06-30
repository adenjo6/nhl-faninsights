// Package season derives the current hockey-season label.
package season

import (
	"fmt"
	"time"
)

// Current returns the season label (e.g. "2025-26") for the given time.
// Hockey seasons span ~September–June, so months before August belong to the
// season that started the previous calendar year. During the off-season this
// returns the season that just finished, which is what fans want to see.
func Current(now time.Time) string {
	y := now.Year()
	if int(now.Month()) >= 8 { // August onward → new season starting this year
		return fmt.Sprintf("%d-%02d", y, (y+1)%100)
	}
	return fmt.Sprintf("%d-%02d", y-1, y%100)
}
