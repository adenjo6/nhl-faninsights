import { useState, useEffect, useMemo } from "react";
import Link from "next/link";

type GameSummary = {
  game_id: number;
  away_team: string;
  home_team: string;
  away_score: number;
  home_score: number;
  game_date: string;
  status: string;
  has_videos: boolean;
};

const SHARKS = "SJS";

type Scoreline = {
  opp: string;
  sharksScore: number;
  oppScore: number;
  sharksHome: boolean;
  result: "W" | "L" | "—";
};

// Reframe a neutral away/home row from the Sharks' point of view: who they
// played, the score, and whether they won. Returns null for the rare game
// that doesn't involve San Jose (defensive — this is a Sharks-only feed).
function scoreline(g: GameSummary): Scoreline | null {
  const sharksHome = g.home_team === SHARKS;
  const sharksAway = g.away_team === SHARKS;
  if (!sharksHome && !sharksAway) return null;
  const sharksScore = sharksHome ? g.home_score : g.away_score;
  const oppScore = sharksHome ? g.away_score : g.home_score;
  const opp = sharksHome ? g.away_team : g.home_team;
  const result =
    sharksScore > oppScore ? "W" : sharksScore < oppScore ? "L" : "—";
  return { opp, sharksScore, oppScore, sharksHome, result };
}

function gameDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function statusLabel(status: string): string {
  return status === "FINAL" || status === "OFF" ? "Final" : status;
}

export default function Home() {
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/games/recent?limit=100`)
      .then((res) => {
        if (!res.ok) throw new Error(`status ${res.status}`);
        return res.json();
      })
      .then((data: GameSummary[]) => {
        setGames(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching games:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Most recent first — the latest game becomes the featured hero.
  const sorted = useMemo(
    () =>
      [...games].sort(
        (a, b) =>
          new Date(b.game_date).getTime() - new Date(a.game_date).getTime()
      ),
    [games]
  );

  // Render helpers live inside the component so styled-jsx scopes their
  // markup to this page's single stylesheet.
  const teamRow = (
    team: string,
    score: number,
    opts: { at?: boolean; isSharks?: boolean; won?: boolean; featured?: boolean }
  ) => (
    <div
      className={`team-row ${opts.isSharks ? "is-sharks" : ""} ${opts.won ? "won" : ""}`}
    >
      <span className="team">
        {opts.at && <span className="at">@ </span>}
        {team}
      </span>
      <span className={`score ${opts.featured ? "big" : ""}`}>{score}</span>
    </div>
  );

  const gameCard = (game: GameSummary, featured = false) => {
    const s = scoreline(game);
    const isFinal = game.status === "FINAL" || game.status === "OFF";
    return (
      <Link
        key={game.game_id}
        href={`/game/${game.game_id}`}
        className={`card ${featured ? "featured" : ""}`}
      >
        <div className="card-top">
          <span className="date">{gameDate(game.game_date)}</span>
          <span className="status">{statusLabel(game.status)}</span>
        </div>

        <div className="teams">
          {s ? (
            <>
              {teamRow(SHARKS, s.sharksScore, {
                at: !s.sharksHome,
                isSharks: true,
                won: isFinal && s.result === "W",
                featured,
              })}
              {teamRow(s.opp, s.oppScore, {
                at: s.sharksHome,
                won: isFinal && s.result === "L",
                featured,
              })}
            </>
          ) : (
            <>
              {teamRow(game.away_team, game.away_score, { featured })}
              {teamRow(game.home_team, game.home_score, { featured })}
            </>
          )}
        </div>

        <div className="card-foot">
          <span className={`dot ${game.has_videos ? "ready" : "wait"}`}>
            {game.has_videos ? "Highlights ready" : "Processing…"}
          </span>
          <span className="go">
            {s && isFinal && (
              <span
                className={`pill ${
                  s.result === "W" ? "win" : s.result === "L" ? "loss" : "tie"
                }`}
              >
                {s.result}
              </span>
            )}
            Recap →
          </span>
        </div>
      </Link>
    );
  };

  return (
    <main className="wrap">
      <header className="masthead">
        <p className="eyebrow">San Jose Sharks · 2025–26</p>
        <h1 className="wordmark">Game Center</h1>
        <p className="lede">
          Recaps, highlights, and fan reaction for every Sharks game.
        </p>
      </header>

      {loading ? (
        <p className="status-line">Loading recent games…</p>
      ) : error ? (
        <div className="notice">
          <p className="notice-h">Can&apos;t reach the game feed.</p>
          <p className="notice-b">
            The backend may still be warming up — refresh in a moment.
          </p>
        </div>
      ) : sorted.length === 0 ? (
        <div className="empty">
          <p>No games yet this season.</p>
          <p className="empty-b">
            Check back after the Sharks&apos; first puck drop.
          </p>
        </div>
      ) : (
        <>
          {gameCard(sorted[0], true)}
          {sorted.length > 1 && (
            <div className="grid">{sorted.slice(1).map((g) => gameCard(g))}</div>
          )}
        </>
      )}

      <style jsx>{styles}</style>
    </main>
  );
}

const styles = `
  .wrap { max-width: 64rem; margin: 0 auto; padding: 2rem 1.25rem 4rem; }

  .masthead { margin-bottom: 1.8rem; }
  .eyebrow {
    font-family: var(--font-display); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.28em; font-size: 0.8rem;
    color: var(--teal); margin: 0 0 0.35rem;
  }
  .wordmark {
    font-family: var(--font-display); font-weight: 700;
    font-size: clamp(2.6rem, 7vw, 4rem); line-height: 0.92;
    letter-spacing: -0.01em; text-transform: uppercase; color: var(--deep);
    margin: 0 0 0.6rem;
  }
  .lede { font-size: 1rem; line-height: 1.5; color: #46605f; margin: 0; max-width: 34rem; }

  .status-line { color: var(--slate); padding-top: 1rem; }

  .grid {
    display: grid; gap: 1rem; margin-top: 1rem;
    grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  }

  .notice {
    border: 1px solid #e0d2c2; background: #fbf6ef; border-radius: 10px;
    padding: 1.2rem 1.4rem;
  }
  .notice-h { font-weight: 600; color: #8a4b12; margin: 0 0 0.3rem; }
  .notice-b { color: #7c6650; margin: 0; font-size: 0.92rem; }

  .empty {
    border: 1px dashed #cfe0de; border-radius: 10px; padding: 2.5rem 1.5rem;
    text-align: center; color: var(--slate);
  }
  .empty p { margin: 0; }
  .empty-b { font-size: 0.9rem; margin-top: 0.4rem !important; color: #8aa1a0; }

  .card {
    display: block; text-decoration: none; color: inherit;
    background: #fff; border: 1px solid var(--line); border-radius: 12px;
    padding: 1.1rem 1.2rem; transition: box-shadow 140ms, border-color 140ms, transform 140ms;
  }
  .card:hover {
    border-color: #bfdedb; box-shadow: 0 8px 24px -14px rgba(0, 59, 65, 0.4);
    transform: translateY(-2px);
  }
  .card:focus-visible { outline: 2px solid var(--teal); outline-offset: 2px; }
  .card.featured {
    padding: 1.5rem 1.6rem; margin-bottom: 0;
    background: linear-gradient(180deg, var(--ice) 0%, #fff 70%);
    border-color: #cfe5e3;
  }

  .card-top {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 0.9rem;
  }
  .date {
    font-family: var(--font-display); font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.78rem;
    color: var(--slate);
  }
  .status {
    font-family: var(--font-display); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.7rem;
    color: #8aa1a0;
  }

  .teams { display: flex; flex-direction: column; gap: 0.35rem; }
  .team-row {
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 1rem;
  }
  .team {
    font-family: var(--font-display); font-weight: 600;
    font-size: 1.3rem; letter-spacing: 0.02em; color: var(--ink);
  }
  .at { color: #a7bbba; font-weight: 500; }
  .is-sharks .team { color: var(--teal); }
  .score {
    font-family: var(--font-display); font-weight: 700;
    font-size: 1.5rem; color: #7c9392; font-variant-numeric: tabular-nums;
  }
  .score.big { font-size: 2.4rem; }
  .won .score { color: var(--deep); }
  .is-sharks.won .score { color: var(--teal); }

  .card-foot {
    display: flex; align-items: center; justify-content: space-between;
    margin-top: 1rem; padding-top: 0.8rem; border-top: 1px solid var(--line);
  }
  .dot {
    font-size: 0.8rem; color: var(--slate);
    display: inline-flex; align-items: center; gap: 0.4rem;
  }
  .dot::before {
    content: ""; width: 7px; height: 7px; border-radius: 999px; background: #c2d2d1;
  }
  .dot.ready { color: var(--teal); }
  .dot.ready::before { background: var(--teal); }
  .go {
    font-family: var(--font-display); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.82rem;
    color: var(--teal); display: inline-flex; align-items: center; gap: 0.5rem;
  }
  .card:hover .go { color: var(--deep); }
  .pill {
    font-family: var(--font-display); font-weight: 700; font-size: 0.72rem;
    width: 1.25rem; height: 1.25rem; border-radius: 999px;
    display: inline-flex; align-items: center; justify-content: center;
    color: #fff;
  }
  .pill.win { background: var(--teal); }
  .pill.loss { background: #9aabaa; }
  .pill.tie { background: var(--orange); }
`;
