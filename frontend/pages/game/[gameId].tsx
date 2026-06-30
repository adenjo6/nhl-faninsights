import { useState, useEffect } from "react";
import { useRouter } from "next/router";

type GameDetail = {
  game_id: number;
  away_team: string;
  home_team: string;
  away_score: number;
  home_score: number;
  game_date_utc: string;
  nhl_video_id?: string;
  professor_hockey_video_id?: string;
  status: string;
  recap_text?: string;
  summary_line?: string;
};

const SHARKS = "SJS";

// Sharks' point of view: opponent, scores, and result. Null if SJS isn't in
// this game (defensive — this is a Sharks-only feed).
function scoreline(g: GameDetail) {
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

const MOOD_EMOJI: Record<string, string> = {
  ecstatic: "🎉",
  elated: "🎉",
  impressed: "😊",
  hopeful: "😊",
  frustrated: "😤",
  disappointed: "😤",
  devastated: "😡",
  angry: "😡",
};

export default function GamePage() {
  const router = useRouter();
  const { gameId } = router.query;
  const [game, setGame] = useState<GameDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recap, setRecap] = useState<{ summary_line: string; recap_text: string } | null>(null);
  const [recapLoading, setRecapLoading] = useState(false);
  const [recapError, setRecapError] = useState<string | null>(null);
  const [sentiment, setSentiment] = useState<any>(null);
  const [redditComments, setRedditComments] = useState<any[]>([]);
  const [redditThreadUrl, setRedditThreadUrl] = useState<string | null>(null);
  const [redditLoading, setRedditLoading] = useState(false);

  useEffect(() => {
    if (!gameId) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/games/${gameId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`status ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setGame(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching game:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [gameId]);

  // Pre-populate the recap if the API already has one stored.
  useEffect(() => {
    if (game?.recap_text && game?.summary_line) {
      setRecap({ summary_line: game.summary_line, recap_text: game.recap_text });
    }
  }, [game]);

  useEffect(() => {
    if (!gameId) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/games/${gameId}/sentiment`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setSentiment(data.sentiment);
      })
      .catch(() => {});
  }, [gameId]);

  useEffect(() => {
    if (!gameId) return;
    setRedditLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/reddit/game/${gameId}/comments?limit=20`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          setRedditComments(data.comments || []);
          setRedditThreadUrl(data.thread_url || null);
        }
      })
      .catch(() => {})
      .finally(() => setRedditLoading(false));
  }, [gameId]);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const generateRecap = async () => {
    if (!game) return;
    setRecapLoading(true);
    setRecapError(null);
    try {
      const res = await fetch(`${apiUrl}/api/recap/${game.game_id}`);
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || `status ${res.status}`);
      }
      const data = await res.json();
      setRecap({ summary_line: data.summary_line, recap_text: data.recap_text });
    } catch (err: any) {
      setRecapError(err.message);
    } finally {
      setRecapLoading(false);
    }
  };

  const Shell = (children: React.ReactNode) => (
    <main className="wrap">
      {children}
      <style jsx>{styles}</style>
    </main>
  );

  if (loading) {
    return Shell(<p className="status-line">Loading game…</p>);
  }

  if (error || !game) {
    return Shell(
      <div className="notice">
        <p className="notice-h">Can&apos;t load this game.</p>
        <p className="notice-b">
          {error ? "It may not exist, or the backend is warming up." : "Game not found."}
        </p>
      </div>
    );
  }

  const s = scoreline(game);
  const isFinal = game.status === "FINAL" || game.status === "OFF";
  const hasVideos = game.nhl_video_id || game.professor_hockey_video_id;
  const dateLabel = new Date(game.game_date_utc).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const sectionHead = (eyebrow: string, title: string, aside?: string) => (
    <div className="sec-head">
      <div>
        <p className="sec-eyebrow">{eyebrow}</p>
        <h2 className="sec-title">{title}</h2>
      </div>
      {aside && <span className="sec-aside">{aside}</span>}
    </div>
  );

  const scoreRow = (team: string, score: number, opts: { at?: boolean; isSharks?: boolean; won?: boolean }) => (
    <div className={`s-row ${opts.isSharks ? "is-sharks" : ""} ${opts.won ? "won" : ""}`}>
      <span className="s-team">
        {opts.at && <span className="s-at">@ </span>}
        {team}
      </span>
      <span className="s-score">{score}</span>
    </div>
  );

  return Shell(
    <>
      {/* Scoreboard */}
      <section className="scoreboard">
        <div className="sb-top">
          <span className="sb-date">{dateLabel}</span>
          <span className={`sb-status ${isFinal ? "final" : ""}`}>
            {isFinal ? "Final" : game.status}
          </span>
        </div>
        <div className="sb-teams">
          {s ? (
            <>
              {scoreRow(SHARKS, s.sharksScore, {
                at: !s.sharksHome,
                isSharks: true,
                won: isFinal && s.result === "W",
              })}
              {scoreRow(s.opp, s.oppScore, {
                at: s.sharksHome,
                won: isFinal && s.result === "L",
              })}
            </>
          ) : (
            <>
              {scoreRow(game.away_team, game.away_score, {})}
              {scoreRow(game.home_team, game.home_score, {})}
            </>
          )}
        </div>
        {s && isFinal && (
          <div className={`sb-result ${s.result === "W" ? "win" : s.result === "L" ? "loss" : ""}`}>
            {s.result === "W" ? "Sharks win" : s.result === "L" ? "Sharks fall" : "Tie"}
          </div>
        )}
      </section>

      {/* AI Recap */}
      <section className="card">
        {sectionHead("The Recap", "Game story", "by Claude")}
        <div className="card-body">
          {recap ? (
            <div className="recap">
              <p className="recap-lead">{recap.summary_line}</p>
              {recap.recap_text.split("\n\n").map((para, i) => (
                <p key={i} className="recap-para">
                  {para}
                </p>
              ))}
            </div>
          ) : (
            <div className="recap-empty">
              {recapError && <p className="inline-err">{recapError}</p>}
              <button className="btn" onClick={generateRecap} disabled={recapLoading}>
                {recapLoading ? "Writing the recap…" : "Generate recap"}
              </button>
              <p className="btn-note">A few seconds — written fresh by Claude.</p>
            </div>
          )}
        </div>
      </section>

      {/* Fan Sentiment */}
      {sentiment && (
        <section className="card">
          {sectionHead("Fan Reaction", "How the fanbase felt", "r/SanJoseSharks")}
          <div className="card-body">
            <div className="mood">
              <span className="mood-emoji">{MOOD_EMOJI[sentiment.fan_mood] || "😐"}</span>
              <span className="mood-label">{sentiment.fan_mood}</span>
              {sentiment.comment_count > 0 && (
                <span className="mood-count">{sentiment.comment_count} comments</span>
              )}
            </div>
            <p className="mood-summary">{sentiment.summary}</p>

            <div className="sbar">
              <div className="sbar-pos" style={{ width: `${sentiment.positive_pct * 100}%` }} />
              <div className="sbar-neu" style={{ width: `${sentiment.neutral_pct * 100}%` }} />
              <div className="sbar-neg" style={{ width: `${sentiment.negative_pct * 100}%` }} />
            </div>
            <div className="sbar-legend">
              <span className="pos">{Math.round(sentiment.positive_pct * 100)}% positive</span>
              <span className="neu">{Math.round(sentiment.neutral_pct * 100)}% neutral</span>
              <span className="neg">{Math.round(sentiment.negative_pct * 100)}% negative</span>
            </div>

            {sentiment.top_themes?.length > 0 && (
              <div className="themes">
                {sentiment.top_themes.map((t: string, i: number) => (
                  <span key={i} className="theme">
                    {t}
                  </span>
                ))}
              </div>
            )}

            {(sentiment.sample_positive?.length > 0 || sentiment.sample_negative?.length > 0) && (
              <div className="quotes">
                {sentiment.sample_positive?.length > 0 && (
                  <div>
                    <p className="q-label pos">Positive takes</p>
                    {sentiment.sample_positive.map((q: string, i: number) => (
                      <p key={i} className="quote">
                        &ldquo;{q}&rdquo;
                      </p>
                    ))}
                  </div>
                )}
                {sentiment.sample_negative?.length > 0 && (
                  <div>
                    <p className="q-label neg">Critical takes</p>
                    {sentiment.sample_negative.map((q: string, i: number) => (
                      <p key={i} className="quote">
                        &ldquo;{q}&rdquo;
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {sentiment.thread_url && (
              <a className="thread-link" href={sentiment.thread_url} target="_blank" rel="noopener noreferrer">
                Full discussion on Reddit ↗
              </a>
            )}
          </div>
        </section>
      )}

      {/* Game Thread */}
      {(redditLoading || redditComments.length > 0) && (
        <section className="card">
          {sectionHead("Game Thread", "Live from the stands", "r/SanJoseSharks")}
          <div className="card-body">
            {redditLoading ? (
              <p className="status-line">Loading comments…</p>
            ) : (
              <>
                <div className="comments">
                  {redditComments.map((c: any, i: number) => (
                    <div key={i} className="comment">
                      <div className="c-meta">
                        <span className="c-author">{c.author}</span>
                        <span className="c-score">{c.score} pts</span>
                        {c.created_utc && (
                          <span className="c-time">
                            {new Date(c.created_utc * 1000).toLocaleString("en-US", {
                              month: "short",
                              day: "numeric",
                              hour: "numeric",
                              minute: "2-digit",
                            })}
                          </span>
                        )}
                      </div>
                      <p className="c-body">{c.body}</p>
                    </div>
                  ))}
                </div>
                {redditThreadUrl && (
                  <a className="thread-link" href={redditThreadUrl} target="_blank" rel="noopener noreferrer">
                    Full thread on Reddit ↗
                  </a>
                )}
              </>
            )}
          </div>
        </section>
      )}

      {/* Videos */}
      {hasVideos ? (
        <section className="card">
          {sectionHead("Highlights", "Watch it back")}
          <div className="card-body videos">
            {game.nhl_video_id && (
              <div className="video">
                <p className="v-label">NHL official recap</p>
                <div className="embed">
                  <iframe
                    src={`https://www.youtube.com/embed/${game.nhl_video_id}`}
                    title="NHL Official Recap"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
              </div>
            )}
            {game.professor_hockey_video_id && (
              <div className="video">
                <p className="v-label">Professor Hockey breakdown</p>
                <div className="embed">
                  <iframe
                    src={`https://www.youtube.com/embed/${game.professor_hockey_video_id}`}
                    title="Professor Hockey Analysis"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
              </div>
            )}
          </div>
        </section>
      ) : (
        <section className="card">
          {sectionHead("Highlights", "Watch it back")}
          <div className="card-body">
            <div className="processing">
              <p className="proc-h">Highlights are still being pulled.</p>
              <p className="proc-b">Videos land a few hours after the final horn — check back soon.</p>
            </div>
          </div>
        </section>
      )}
    </>
  );
}

const styles = `
  .wrap {
    max-width: 52rem; margin: 0 auto; padding: 2rem 1.25rem 4rem;
    font-family: var(--font-body); color: var(--ink);
  }
  .status-line { color: var(--slate); }

  .notice {
    border: 1px solid #e0d2c2; background: #fbf6ef; border-radius: 10px;
    padding: 1.2rem 1.4rem;
  }
  .notice-h { font-weight: 600; color: #8a4b12; margin: 0 0 0.3rem; }
  .notice-b { color: #7c6650; margin: 0; font-size: 0.92rem; }

  /* Scoreboard hero */
  .scoreboard {
    background: linear-gradient(180deg, var(--ice) 0%, #fff 75%);
    border: 1px solid #cfe5e3; border-radius: 14px;
    padding: 1.5rem 1.7rem; margin-bottom: 1.4rem;
  }
  .sb-top {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1.1rem;
  }
  .sb-date {
    font-family: var(--font-display); font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.82rem;
    color: var(--slate);
  }
  .sb-status {
    font-family: var(--font-display); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.74rem;
    color: #8aa1a0;
  }
  .sb-teams { display: flex; flex-direction: column; gap: 0.4rem; }
  .s-row {
    display: flex; align-items: baseline; justify-content: space-between; gap: 1rem;
  }
  .s-team {
    font-family: var(--font-display); font-weight: 600;
    font-size: 1.7rem; letter-spacing: 0.02em; color: var(--ink);
  }
  .s-at { color: #a7bbba; font-weight: 500; }
  .is-sharks .s-team { color: var(--teal); }
  .s-score {
    font-family: var(--font-display); font-weight: 700;
    font-size: 2.6rem; line-height: 1; color: #7c9392;
    font-variant-numeric: tabular-nums;
  }
  .won .s-score { color: var(--deep); }
  .is-sharks.won .s-score { color: var(--teal); }
  .sb-result {
    margin-top: 1rem; padding-top: 0.9rem; border-top: 1px solid #d6e7e5;
    font-family: var(--font-display); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.84rem;
  }
  .sb-result.win { color: var(--teal); }
  .sb-result.loss { color: #9aabaa; }

  /* Section cards */
  .card {
    background: #fff; border: 1px solid var(--line); border-radius: 14px;
    margin-bottom: 1.4rem; overflow: hidden;
  }
  .sec-head {
    display: flex; align-items: flex-end; justify-content: space-between;
    gap: 1rem; padding: 1.1rem 1.4rem 0.9rem;
    border-bottom: 2px solid var(--deep);
  }
  .sec-eyebrow {
    font-family: var(--font-display); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.2em; font-size: 0.72rem;
    color: var(--teal); margin: 0 0 0.15rem;
  }
  .sec-title {
    font-family: var(--font-display); font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.01em; font-size: 1.5rem;
    line-height: 1; color: var(--deep); margin: 0;
  }
  .sec-aside {
    font-family: var(--font-display); font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.72rem;
    color: #8aa1a0; white-space: nowrap;
  }
  .card-body { padding: 1.3rem 1.4rem; }

  /* Recap */
  .recap-lead {
    font-family: var(--font-display); font-weight: 600;
    font-size: 1.5rem; line-height: 1.15; color: var(--deep);
    margin: 0 0 1rem;
  }
  .recap-para { line-height: 1.6; color: #2f4544; margin: 0 0 0.9rem; }
  .recap-para:last-child { margin-bottom: 0; }
  .recap-empty { text-align: center; padding: 0.6rem 0; }
  .inline-err { color: #b0432b; margin: 0 0 0.8rem; font-size: 0.92rem; }
  .btn {
    font-family: var(--font-display); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.9rem;
    color: #fff; background: var(--teal); border: none; border-radius: 8px;
    padding: 0.7rem 1.4rem; cursor: pointer; transition: background 130ms;
  }
  .btn:hover { background: var(--deep); }
  .btn:disabled { opacity: 0.55; cursor: not-allowed; }
  .btn:focus-visible { outline: 2px solid var(--teal); outline-offset: 2px; }
  .btn-note { color: var(--slate); font-size: 0.82rem; margin: 0.7rem 0 0; }

  /* Sentiment */
  .mood { display: flex; align-items: center; gap: 0.7rem; margin-bottom: 0.7rem; }
  .mood-emoji { font-size: 1.8rem; line-height: 1; }
  .mood-label {
    font-family: var(--font-display); font-weight: 700; font-size: 1.2rem;
    text-transform: capitalize; color: var(--ink);
  }
  .mood-count { color: var(--slate); font-size: 0.85rem; }
  .mood-summary { line-height: 1.55; color: #2f4544; margin: 0 0 1.2rem; }
  .sbar {
    display: flex; height: 0.6rem; border-radius: 999px; overflow: hidden;
    margin-bottom: 0.5rem; background: #eef3f2;
  }
  .sbar-pos { background: var(--teal); }
  .sbar-neu { background: #cdd9d8; }
  .sbar-neg { background: #c65c3c; }
  .sbar-legend {
    display: flex; justify-content: space-between; font-size: 0.8rem;
    color: var(--slate); margin-bottom: 1.2rem;
  }
  .sbar-legend .pos { color: var(--teal); }
  .sbar-legend .neg { color: #b0432b; }
  .themes { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-bottom: 1.2rem; }
  .theme {
    font-family: var(--font-display); font-weight: 600; font-size: 0.8rem;
    letter-spacing: 0.03em; color: #34504f; background: var(--mist);
    border: 1px solid #d3e0df; border-radius: 999px; padding: 0.25rem 0.7rem;
  }
  .quotes { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; }
  .q-label {
    font-family: var(--font-display); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.74rem;
    margin: 0 0 0.5rem;
  }
  .q-label.pos { color: var(--teal); }
  .q-label.neg { color: #b0432b; }
  .quote {
    font-size: 0.9rem; line-height: 1.45; color: #506665; font-style: italic;
    margin: 0 0 0.5rem;
  }
  .thread-link {
    display: inline-block; margin-top: 1.1rem;
    font-family: var(--font-display); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.8rem;
    color: var(--teal); text-decoration: none;
  }
  .thread-link:hover { color: var(--deep); }

  /* Comments */
  .comments { max-height: 34rem; overflow-y: auto; }
  .comment { border-bottom: 1px solid var(--line); padding: 0.7rem 0; }
  .comment:first-child { padding-top: 0; }
  .comment:last-child { border-bottom: none; }
  .c-meta { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.25rem; }
  .c-author { font-weight: 600; font-size: 0.88rem; color: var(--ink); }
  .c-score {
    font-family: var(--font-display); font-weight: 600; font-size: 0.78rem;
    color: var(--orange-ink);
  }
  .c-time { font-size: 0.74rem; color: #a7bbba; }
  .c-body { font-size: 0.9rem; line-height: 1.5; color: #36504e; margin: 0; white-space: pre-line; }

  /* Videos */
  .videos { display: flex; flex-direction: column; gap: 1.4rem; }
  .v-label {
    font-family: var(--font-display); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.78rem;
    color: var(--slate); margin: 0 0 0.6rem;
  }
  .embed { position: relative; width: 100%; padding-bottom: 56.25%; border-radius: 10px; overflow: hidden; background: #000; }
  .embed iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }

  .processing { text-align: center; padding: 1.4rem 0; }
  .proc-h { font-family: var(--font-display); font-weight: 600; font-size: 1.1rem; color: var(--deep); margin: 0 0 0.4rem; text-transform: uppercase; letter-spacing: 0.04em; }
  .proc-b { color: var(--slate); margin: 0; font-size: 0.92rem; }

  @media (max-width: 560px) {
    .quotes { grid-template-columns: 1fr; }
    .s-score { font-size: 2.1rem; }
  }
`;
