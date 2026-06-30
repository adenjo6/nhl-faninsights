import { useState, useEffect, useMemo } from "react";
import Link from "next/link";

type SeasonStats = {
  season: string;
  games_played: number;
  goals: number;
  assists: number;
  points: number;
  plus_minus: number;
  pim: number;
  updated_at: string;
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

// Sortable numeric stat columns. `key` indexes into current_season; players
// without live stats (NCAA/Euro/goalie link-outs) sort to the bottom.
const STAT_COLUMNS: { key: NumericStatKey; label: string; title: string }[] = [
  { key: "games_played", label: "GP", title: "Games played" },
  { key: "goals", label: "G", title: "Goals" },
  { key: "assists", label: "A", title: "Assists" },
  { key: "points", label: "P", title: "Points" },
  { key: "plus_minus", label: "+/-", title: "Plus/minus" },
  { key: "pim", label: "PIM", title: "Penalty minutes" },
];

export default function Prospects() {
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [position, setPosition] = useState<string>("");
  const [league, setLeague] = useState<string>("");
  const [sortKey, setSortKey] = useState<NumericStatKey>("points");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    fetch(`${apiUrl}/api/prospects`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Failed to fetch prospects: ${res.status}`);
        }
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

  // Filter options are derived from the data so they always match what's
  // actually in the roster (no hard-coded league/position lists to drift).
  const positions = useMemo(
    () => Array.from(new Set(prospects.map((p) => p.position))).sort(),
    [prospects]
  );
  const leagues = useMemo(
    () => Array.from(new Set(prospects.map((p) => p.league))).sort(),
    [prospects]
  );

  const rows = useMemo(() => {
    const filtered = prospects.filter(
      (p) =>
        (!position || p.position === position) &&
        (!league || p.league === league)
    );
    // Sort by the chosen stat descending; link-out players (no current_season)
    // always sink to the bottom regardless of column.
    return [...filtered].sort((a, b) => {
      const av = a.current_season?.[sortKey];
      const bv = b.current_season?.[sortKey];
      if (av == null && bv == null) return a.full_name.localeCompare(b.full_name);
      if (av == null) return 1;
      if (bv == null) return -1;
      return bv - av;
    });
  }, [prospects, position, league, sortKey]);

  if (loading) {
    return (
      <main className="max-w-6xl mx-auto p-6">
        <h1 className="text-4xl font-bold mb-8 text-teal-600">🦈 Sharks Prospects</h1>
        <p className="text-gray-600">Loading prospects...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="max-w-6xl mx-auto p-6">
        <h1 className="text-4xl font-bold mb-8 text-teal-600">🦈 Sharks Prospects</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
          <p className="text-sm text-red-600 mt-2">
            Make sure the backend is running at{" "}
            {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-6xl mx-auto p-6">
      <header className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-4xl font-bold text-teal-600">🦈 Sharks Prospects</h1>
          <Link href="/" className="text-teal-600 font-medium hover:underline">
            ← Games
          </Link>
        </div>
        <p className="text-gray-600">
          San Jose Sharks prospect pool with live current-season stats (CHL/AHL).
        </p>
      </header>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <label className="text-sm">
          <span className="block text-gray-500 mb-1">Position</span>
          <select
            value={position}
            onChange={(e) => setPosition(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 bg-white"
          >
            <option value="">All</option>
            {positions.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="block text-gray-500 mb-1">League</span>
          <select
            value={league}
            onChange={(e) => setLeague(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 bg-white"
          >
            <option value="">All</option>
            {leagues.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </label>
      </div>

      {rows.length === 0 ? (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-gray-600">No prospects match these filters.</p>
        </div>
      ) : (
        <div className="overflow-x-auto border border-gray-200 rounded-lg bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-gray-500 text-left">
                <th className="px-4 py-3 font-medium">Player</th>
                <th className="px-4 py-3 font-medium">Pos</th>
                <th className="px-4 py-3 font-medium">League</th>
                <th className="px-4 py-3 font-medium">Team</th>
                {STAT_COLUMNS.map((col) => {
                  const active = sortKey === col.key;
                  return (
                    <th
                      key={col.key}
                      title={`${col.title} — click to sort`}
                      onClick={() => setSortKey(col.key)}
                      className={`px-3 py-3 font-medium text-right cursor-pointer select-none hover:text-teal-600 ${
                        active ? "text-teal-600" : ""
                      }`}
                    >
                      {col.label}
                      {active ? " ▾" : ""}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr
                  key={p.id}
                  className="border-b border-gray-100 last:border-0 hover:bg-gray-50"
                >
                  <td className="px-4 py-3 font-medium">
                    {p.elite_prospects_url ? (
                      <a
                        href={p.elite_prospects_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-teal-700 hover:underline"
                      >
                        {p.full_name}
                      </a>
                    ) : (
                      p.full_name
                    )}
                    {p.draft_year ? (
                      <span className="text-gray-400 text-xs ml-2">
                        &apos;{String(p.draft_year).slice(2)}
                        {p.draft_overall ? ` #${p.draft_overall}` : ""}
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{p.position}</td>
                  <td className="px-4 py-3 text-gray-700">{p.league}</td>
                  <td className="px-4 py-3 text-gray-500">{p.team_name || "—"}</td>
                  {STAT_COLUMNS.map((col) => (
                    <td
                      key={col.key}
                      className={`px-3 py-3 text-right tabular-nums ${
                        sortKey === col.key ? "font-semibold text-gray-900" : "text-gray-700"
                      }`}
                    >
                      {p.current_season ? p.current_season[col.key] : "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-gray-400 mt-4">
        Players without live stats (goalies, NCAA/European) link out to Elite
        Prospects. Stats refresh daily.
      </p>
    </main>
  );
}
