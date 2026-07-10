import { useState, useEffect, useMemo } from "react";

// ot_losses/gaa/sv_pct are null when the source doesn't report them —
// unknown renders as an em dash, never as 0 (a 0.00 GAA would read as a
// league-best line, not missing data).
type GoalieStats = {
  wins: number;
  losses: number;
  ot_losses: number | null;
  shutouts: number;
  saves: number;
  shots: number;
  gaa: number | null;
  sv_pct: number | null;
};

type SeasonStats = {
  season: string;
  games_played: number;
  goals: number;
  assists: number;
  points: number;
  plus_minus: number;
  pim: number;
  updated_at: string;
  // Set only for goalies; its presence marks the line as a goalie line (the
  // skater counters above stay 0).
  goalie?: GoalieStats | null;
};

type Prospect = {
  id: number;
  full_name: string;
  position: string;
  draft_year: number | null;
  draft_overall: number | null;
  league: string;
  team_name: string | null;
  elite_prospects_url: string | null;
  has_live_stats: boolean;
  current_season: SeasonStats | null;
};

// The numeric stat fields only — excludes the string members (season,
// updated_at) so sorting arithmetic stays type-safe.
type NumericStatKey =
  | "games_played"
  | "goals"
  | "assists"
  | "points"
  | "plus_minus"
  | "pim";

const STAT_COLUMNS: { key: NumericStatKey; label: string; title: string }[] = [
  { key: "games_played", label: "GP", title: "Games played" },
  { key: "goals", label: "G", title: "Goals" },
  { key: "assists", label: "A", title: "Assists" },
  { key: "points", label: "P", title: "Points" },
  { key: "plus_minus", label: "+/−", title: "Plus / minus" },
  { key: "pim", label: "PIM", title: "Penalty minutes" },
];

// "2h ago" style freshness for the stat strip. Runs in the browser, so Date is
// available; returns null on missing/unparseable input so the strip hides it.
function timeAgo(iso?: string): string | null {
  if (!iso) return null;
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return null;
  const mins = Math.max(0, Math.floor((Date.now() - then) / 60000));
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function Prospects() {
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const [position, setPosition] = useState<string>("");
  const [league, setLeague] = useState<string>("");
  const [sortKey, setSortKey] = useState<NumericStatKey>("points");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/prospects`)
      .then((res) => {
        if (!res.ok) throw new Error(`status ${res.status}`);
        return res.json();
      })
      .then((data: Prospect[]) => {
        setProspects(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching prospects:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Trigger the bar-gauge grow-in once data has painted.
  useEffect(() => {
    if (!loading && !error) {
      const id = requestAnimationFrame(() => setMounted(true));
      return () => cancelAnimationFrame(id);
    }
  }, [loading, error]);

  // Filter options are derived from the data so they always reflect the actual
  // roster — no hard-coded league/position lists to drift out of sync.
  const positions = useMemo(
    () => Array.from(new Set(prospects.map((p) => p.position))).sort(),
    [prospects]
  );
  const leagues = useMemo(
    () => Array.from(new Set(prospects.map((p) => p.league))).sort(),
    [prospects]
  );

  const filtered = useMemo(
    () =>
      prospects.filter(
        (p) =>
          (!position || p.position === position) &&
          (!league || p.league === league)
      ),
    [prospects, position, league]
  );

  // Three cohorts: skaters with a live feed (ranked by the chosen stat),
  // goalies with a live feed (the crease, fixed GP order), and the watch list
  // (NCAA / Europe / unfeedable goalies) with no current-season line.
  const skaters = useMemo(
    () =>
      filtered
        .filter((p) => p.current_season && !p.current_season.goalie)
        .sort(
          (a, b) =>
            (b.current_season![sortKey] - a.current_season![sortKey]) ||
            a.full_name.localeCompare(b.full_name)
        ),
    [filtered, sortKey]
  );
  const goalies = useMemo(
    () =>
      filtered
        .filter((p) => p.current_season?.goalie)
        .sort(
          (a, b) =>
            (b.current_season!.games_played - a.current_season!.games_played) ||
            a.full_name.localeCompare(b.full_name)
        ),
    [filtered]
  );
  const watching = useMemo(
    () =>
      filtered
        .filter((p) => !p.current_season)
        .sort((a, b) => a.full_name.localeCompare(b.full_name)),
    [filtered]
  );

  // Pool leader in the active stat — the denominator for every bar-gauge.
  const leaderValue = useMemo(
    () => skaters.reduce((m, p) => Math.max(m, p.current_season![sortKey]), 0),
    [skaters, sortKey]
  );
  const freshness = useMemo(() => {
    const latest = prospects
      .map((p) => p.current_season?.updated_at)
      .filter(Boolean)
      .sort()
      .pop();
    return timeAgo(latest);
  }, [prospects]);

  const clearFilters = () => {
    setPosition("");
    setLeague("");
  };

  // Defined inside the component so styled-jsx scopes its markup. Used by both
  // the skater rows and the watch list.
  const renderName = (p: Prospect) => {
    const draft = p.draft_year
      ? `'${String(p.draft_year).slice(2)}${
          p.draft_overall ? ` · #${p.draft_overall}` : ""
        }`
      : null;
    return (
      <span className="namecell">
        {p.elite_prospects_url ? (
          <a
            className="name"
            href={p.elite_prospects_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {p.full_name}
            <span className="scout" aria-hidden="true">
              ↗
            </span>
          </a>
        ) : (
          <span className="name">{p.full_name}</span>
        )}
        {draft && <span className="draft">{draft}</span>}
      </span>
    );
  };

  const Shell = (children: React.ReactNode) => (
    <div className="pool">
      {children}
      <style jsx>{styles}</style>
    </div>
  );

  if (loading) {
    return Shell(
      <main className="wrap">
        <p className="status">Reading the scouting board…</p>
      </main>
    );
  }

  if (error) {
    return Shell(
      <main className="wrap">
        <p className="eyebrow">The Pipeline</p>
        <h1 className="wordmark">Prospect Pool</h1>
        <div className="notice">
          <p className="notice-h">Can&apos;t reach the prospect feed.</p>
          <p className="notice-b">
            The service may still be warming up — refresh in a moment.
          </p>
        </div>
      </main>
    );
  }

  return Shell(
    <main className="wrap">
      <header className="masthead">
        <p className="eyebrow">The Pipeline · 2025–26</p>
        <h1 className="wordmark">Prospect Pool</h1>
        <p className="lede">
          The Sharks&apos; future, tracked across the CHL and AHL with live
          current-season stats.
        </p>
        <dl className="strip">
          <div className="stat">
            <dd>{prospects.length}</dd>
            <dt>in the system</dt>
          </div>
          <div className="stat">
            <dd>{leagues.length}</dd>
            <dt>leagues</dt>
          </div>
          {freshness && (
            <div className="stat">
              <dd>{freshness}</dd>
              <dt>stats updated</dt>
            </div>
          )}
        </dl>
      </header>

      <div className="filters">
        {[
          { label: "Position", value: position, options: positions, set: setPosition },
          { label: "League", value: league, options: leagues, set: setLeague },
        ].map((f) => (
          <div className="filter" key={f.label}>
            <span className="filter-label">{f.label}</span>
            <div className="chips">
              <button
                className={`chip ${f.value === "" ? "on" : ""}`}
                aria-pressed={f.value === ""}
                onClick={() => f.set("")}
              >
                All
              </button>
              {f.options.map((o) => (
                <button
                  key={o}
                  className={`chip ${f.value === o ? "on" : ""}`}
                  aria-pressed={f.value === o}
                  onClick={() => f.set(o)}
                >
                  {o}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="empty">
          <p>No one in the pool fits those filters.</p>
          <button className="link-btn" onClick={clearFilters}>
            Clear filters
          </button>
        </div>
      ) : (
        <div className="board-scroll">
          {skaters.length > 0 && (
          <table className="board">
            <thead>
              <tr>
                <th className="col-rank" scope="col">
                  #
                </th>
                <th className="col-player" scope="col">
                  Player
                </th>
                <th className="col-meta" scope="col">
                  Pos
                </th>
                <th className="col-meta" scope="col">
                  Lg
                </th>
                <th className="col-team" scope="col">
                  Team
                </th>
                {STAT_COLUMNS.map((col) => {
                  const active = sortKey === col.key;
                  return (
                    <th
                      key={col.key}
                      scope="col"
                      className="col-stat"
                      aria-sort={active ? "descending" : "none"}
                    >
                      <button
                        className={`sort ${active ? "is-active" : ""}`}
                        onClick={() => setSortKey(col.key)}
                        title={`${col.title} — sort`}
                      >
                        {col.label}
                        <span className="caret">{active ? "▾" : ""}</span>
                      </button>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {skaters.map((p, i) => {
                const s = p.current_season!;
                const isLeader = i === 0 && s[sortKey] === leaderValue && leaderValue > 0;
                const pct = leaderValue > 0 ? (s[sortKey] / leaderValue) * 100 : 0;
                return (
                  <tr key={p.id} className="row">
                    <td className="col-rank rank">{i + 1}</td>
                    <td className="col-player">
                      {renderName(p)}
                    </td>
                    <td className="col-meta pos">{p.position}</td>
                    <td className="col-meta lg">{p.league}</td>
                    <td className="col-team team">{p.team_name || "—"}</td>
                    {STAT_COLUMNS.map((col) => {
                      const active = sortKey === col.key;
                      if (col.key === "points") {
                        return (
                          <td key={col.key} className="col-stat gaugecell">
                            <span
                              className={`gauge ${isLeader ? "lead" : ""}`}
                              style={{
                                width: mounted ? `${pct}%` : "0%",
                                transitionDelay: `${Math.min(i, 12) * 40}ms`,
                              }}
                              aria-hidden="true"
                            />
                            <span className={`gaugenum ${isLeader ? "lead" : ""}`}>
                              {s.points}
                            </span>
                          </td>
                        );
                      }
                      return (
                        <td
                          key={col.key}
                          className={`col-stat statnum ${active ? "is-active" : ""}`}
                        >
                          {s[col.key]}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
          )}

          {goalies.length > 0 && (
            <>
              <p className="section-h">In the Crease</p>
              <table className="board">
                <thead>
                  <tr>
                    <th className="col-rank" scope="col">#</th>
                    <th className="col-player" scope="col">Player</th>
                    <th className="col-meta" scope="col">Lg</th>
                    <th className="col-team" scope="col">Team</th>
                    <th className="col-stat" scope="col" title="Games played">GP</th>
                    <th className="col-stat" scope="col" title="Wins – losses – OT/SO losses">Record</th>
                    <th className="col-stat" scope="col" title="Goals-against average">GAA</th>
                    <th className="col-stat" scope="col" title="Save percentage">SV%</th>
                    <th className="col-stat" scope="col" title="Shutouts">SO</th>
                  </tr>
                </thead>
                <tbody>
                  {goalies.map((p, i) => {
                    const s = p.current_season!;
                    const g = s.goalie!;
                    return (
                      <tr key={p.id} className="row">
                        <td className="col-rank rank">{i + 1}</td>
                        <td className="col-player">{renderName(p)}</td>
                        <td className="col-meta lg">{p.league}</td>
                        <td className="col-team team">{p.team_name || "—"}</td>
                        <td className="col-stat statnum">{s.games_played}</td>
                        <td className="col-stat statnum">
                          {g.wins}-{g.losses}
                          {g.ot_losses != null ? `-${g.ot_losses}` : ""}
                        </td>
                        <td className="col-stat statnum">
                          {g.gaa != null ? g.gaa.toFixed(2) : "—"}
                        </td>
                        <td className="col-stat statnum">
                          {g.sv_pct != null
                            ? g.sv_pct.toFixed(3).replace(/^0\./, ".")
                            : "—"}
                        </td>
                        <td className="col-stat statnum">{g.shutouts}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </>
          )}

          {watching.length > 0 && (
            <>
              <p className="section-h muted">Watching · no live feed yet</p>
              <table className="board">
                <thead>
                  <tr>
                    <th className="col-rank" scope="col"></th>
                    <th className="col-player" scope="col">Player</th>
                    <th className="col-meta" scope="col">Pos</th>
                    <th className="col-meta" scope="col">Lg</th>
                    <th className="col-team" scope="col">Team</th>
                    <th className="col-stat" scope="col"></th>
                  </tr>
                </thead>
                <tbody>
                  {watching.map((p) => (
                    <tr key={p.id} className="row watch">
                      <td className="col-rank rank">·</td>
                      <td className="col-player">
                        {renderName(p)}
                      </td>
                      <td className="col-meta pos">{p.position}</td>
                      <td className="col-meta lg">{p.league}</td>
                      <td className="col-team team">{p.team_name || "—"}</td>
                      <td className="col-stat statnum dash">—</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      <p className="footnote">
        CHL and AHL stats are live, refreshed daily. NCAA, USports, and
        European lines are final 2025–26 season totals. Every player links
        out to Elite Prospects.
      </p>
    </main>
  );
}

const styles = `
  .pool {
    background: linear-gradient(180deg, #ECF4F3 0%, #fff 320px);
    min-height: calc(100vh - 3.5rem);
    color: #0E2123;
    font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
  }
  .wrap { max-width: 64rem; margin: 0 auto; padding: 2rem 1.25rem 4rem; }

  .status { color: #5B7173; font-size: 0.95rem; padding-top: 2rem; }

  .masthead { margin-bottom: 2rem; }
  .eyebrow {
    font-family: 'Saira Condensed', sans-serif; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.34em; font-size: 0.82rem;
    color: #006D75; margin: 0 0 0.35rem;
  }
  .wordmark {
    font-family: 'Saira Condensed', sans-serif; font-weight: 700;
    font-size: clamp(2.8rem, 8vw, 4.5rem); line-height: 0.92;
    letter-spacing: -0.01em; text-transform: uppercase; color: #003B41;
    margin: 0 0 0.7rem;
  }
  .lede {
    font-size: 1rem; line-height: 1.5; color: #46605F; max-width: 34rem;
    margin: 0 0 1.4rem;
  }
  .strip {
    display: flex; gap: 2.2rem; margin: 0;
    border-top: 2px solid #003B41; padding-top: 0.9rem;
  }
  .strip .stat dd {
    font-family: 'Saira Condensed', sans-serif; font-weight: 700;
    font-size: 1.7rem; line-height: 1; color: #003B41; margin: 0;
    font-variant-numeric: tabular-nums;
  }
  .strip .stat dt {
    font-family: 'Saira Condensed', sans-serif; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.7rem;
    color: #7C9392; margin-top: 0.2rem;
  }

  .filters {
    display: flex; flex-direction: column; gap: 0.8rem;
    margin-bottom: 1.4rem;
  }
  .filter { display: flex; align-items: center; gap: 0.9rem; flex-wrap: wrap; }
  .filter-label {
    font-family: 'Saira Condensed', sans-serif; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.74rem;
    color: #5B7173; width: 4.6rem; flex: none;
  }
  .chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .chip {
    font-family: 'Saira Condensed', sans-serif; font-weight: 600;
    font-size: 0.82rem; letter-spacing: 0.04em;
    padding: 0.28rem 0.72rem; border-radius: 999px;
    border: 1px solid #D3E0DF; background: #fff; color: #4A6160;
    cursor: pointer; transition: background 120ms, color 120ms, border-color 120ms;
  }
  .chip:hover { border-color: #006D75; color: #006D75; }
  .chip.on { background: #003B41; border-color: #003B41; color: #fff; }
  .chip:focus-visible { outline: 2px solid #006D75; outline-offset: 2px; }

  .namecell { display: flex; align-items: baseline; gap: 0.6rem; min-width: 0; }
  .name {
    font-weight: 600; color: #0E2123; text-decoration: none;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  a.name:hover { color: #006D75; }
  a.name:focus-visible { outline: 2px solid #006D75; outline-offset: 2px; border-radius: 2px; }
  .scout { font-size: 0.72em; color: #9DB3B2; margin-left: 0.28rem; }
  a.name:hover .scout { color: #EA7600; }
  .draft {
    font-family: 'Saira Condensed', sans-serif; font-weight: 500;
    font-size: 0.72rem; letter-spacing: 0.04em; color: #8AA1A0;
    flex: none; white-space: nowrap;
  }

  .board-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .board {
    width: 100%; border-collapse: collapse; min-width: 640px;
  }
  .board thead th {
    font-family: 'Saira Condensed', sans-serif; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.76rem;
    color: #7C9392; text-align: left; padding: 0 0.55rem 0.6rem;
    border-bottom: 2px solid #003B41; white-space: nowrap;
  }
  .col-rank { width: 2.2rem; text-align: center !important; }
  .col-stat { text-align: right !important; }
  .col-team { color: #5B7173; }

  .sort {
    font: inherit; color: inherit; background: none; border: none;
    cursor: pointer; padding: 0; text-transform: inherit;
    letter-spacing: inherit; display: inline-flex; align-items: baseline;
    gap: 0.12rem;
  }
  .sort:hover { color: #006D75; }
  .sort.is-active { color: #003B41; }
  .sort:focus-visible { outline: 2px solid #006D75; outline-offset: 2px; }
  .caret { color: #EA7600; font-size: 0.7em; }

  .row { border-bottom: 1px solid #E6EEED; }
  .row td { padding: 0.7rem 0.55rem; vertical-align: middle; }
  .row:hover { background: #F4FAF9; }
  .row .col-player { position: relative; }
  .row:hover .col-player::before,
  .row:focus-within .col-player::before {
    content: ""; position: absolute; left: -1.25rem; top: 0; bottom: 0;
    width: 3px; background: #006D75;
  }

  .rank {
    font-family: 'Saira Condensed', sans-serif; font-weight: 600;
    font-size: 0.95rem; color: #A7BBBA; text-align: center;
    font-variant-numeric: tabular-nums;
  }
  .pos {
    font-family: 'Saira Condensed', sans-serif; font-weight: 600;
    font-size: 0.92rem; color: #34504F;
  }
  .lg {
    font-family: 'Saira Condensed', sans-serif; font-weight: 500;
    font-size: 0.86rem; letter-spacing: 0.03em; color: #5B7173;
  }
  .team {
    font-size: 0.9rem; color: #5B7173; white-space: nowrap;
    max-width: 12rem; overflow: hidden; text-overflow: ellipsis;
  }

  .statnum {
    text-align: right; font-size: 0.95rem; color: #38514F;
    font-variant-numeric: tabular-nums;
  }
  .statnum.is-active { color: #0E2123; font-weight: 600; }
  .statnum.dash { color: #C2D2D1; }

  /* Signature: the Points cell is a bar-gauge against the pool leader. */
  .gaugecell {
    position: relative; text-align: right; min-width: 4.2rem;
    padding-right: 0.7rem !important;
  }
  .gauge {
    position: absolute; left: 0; top: 50%; transform: translateY(-50%);
    height: 1.6rem; background: rgba(0, 109, 117, 0.16);
    border-left: 2px solid #006D75; border-radius: 1px;
  }
  .gauge.lead { background: rgba(234, 118, 0, 0.18); border-left-color: #EA7600; }
  .gaugenum {
    position: relative; font-family: 'Saira Condensed', sans-serif;
    font-weight: 700; font-size: 1.15rem; color: #003B41;
    font-variant-numeric: tabular-nums;
  }
  .gaugenum.lead { color: #C2540A; }

  .section-h {
    font-family: 'Saira Condensed', sans-serif; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.16em; font-size: 0.72rem;
    color: #006D75; margin: 1.6rem 0 0.5rem;
  }
  .section-h.muted { color: #9DB3B2; }
  .row.watch td { padding-top: 0.6rem; padding-bottom: 0.6rem; }

  .empty {
    border: 1px dashed #CFE0DE; border-radius: 8px; padding: 2.5rem 1.5rem;
    text-align: center; color: #5B7173;
  }
  .empty p { margin: 0 0 0.8rem; }
  .link-btn {
    font-family: 'Saira Condensed', sans-serif; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.82rem;
    color: #006D75; background: none; border: none; cursor: pointer;
    padding: 0.2rem;
  }
  .link-btn:hover { color: #003B41; text-decoration: underline; }
  .link-btn:focus-visible { outline: 2px solid #006D75; outline-offset: 2px; }

  .notice {
    border: 1px solid #E0D2C2; background: #FBF6EF; border-radius: 8px;
    padding: 1.2rem 1.4rem; margin-top: 1.5rem;
  }
  .notice-h { font-weight: 600; color: #8A4B12; margin: 0 0 0.3rem; }
  .notice-b { color: #7C6650; margin: 0; font-size: 0.92rem; }

  .footnote {
    margin-top: 1.6rem; font-size: 0.78rem; line-height: 1.5;
    color: #97ABAA; max-width: 38rem;
  }

  @media (prefers-reduced-motion: no-preference) {
    .gauge { transition: width 700ms cubic-bezier(0.22, 1, 0.36, 1); }
  }

  @media (max-width: 560px) {
    .strip { gap: 1.4rem; }
    .filter-label { width: auto; }
  }
`;
