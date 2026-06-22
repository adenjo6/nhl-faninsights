import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Link from "next/link";

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

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    fetch(`${apiUrl}/api/games/${gameId}`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to fetch game: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        setGame(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching game:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [gameId]);

  // If the game already has a recap from the API, pre-populate
  useEffect(() => {
    if (game?.recap_text && game?.summary_line) {
      setRecap({ summary_line: game.summary_line, recap_text: game.recap_text });
    }
  }, [game]);

  // Fetch Reddit sentiment
  useEffect(() => {
    if (!gameId) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${apiUrl}/api/games/${gameId}/sentiment`)
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) setSentiment(data.sentiment); })
      .catch(() => {});
  }, [gameId]);

  // Fetch Reddit comments
  useEffect(() => {
    if (!gameId) return;
    setRedditLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${apiUrl}/api/reddit/game/${gameId}/comments?limit=20`)
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data) {
          setRedditComments(data.comments || []);
          setRedditThreadUrl(data.thread_url || null);
        }
      })
      .catch(() => {})
      .finally(() => setRedditLoading(false));
  }, [gameId]);

  if (loading) {
    return (
      <main className="max-w-6xl mx-auto p-6">
        <Link href="/" className="text-teal-600 hover:text-teal-800 mb-4 inline-block">
          ← Back to Games
        </Link>
        <p className="text-gray-600">Loading game...</p>
      </main>
    );
  }

  if (error || !game) {
    return (
      <main className="max-w-6xl mx-auto p-6">
        <Link href="/" className="text-teal-600 hover:text-teal-800 mb-4 inline-block">
          ← Back to Games
        </Link>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-4">
          <p className="text-red-800">Error: {error || 'Game not found'}</p>
        </div>
      </main>
    );
  }

  const hasVideos = game.nhl_video_id || game.professor_hockey_video_id;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const generateRecap = async () => {
    setRecapLoading(true);
    setRecapError(null);
    try {
      const res = await fetch(`${apiUrl}/api/recap/${game.game_id}`);
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || `Failed to generate recap: ${res.status}`);
      }
      const data = await res.json();
      setRecap({ summary_line: data.summary_line, recap_text: data.recap_text });
    } catch (err: any) {
      setRecapError(err.message);
    } finally {
      setRecapLoading(false);
    }
  };

  return (
    <main className="max-w-6xl mx-auto p-6">
      <Link href="/" className="text-teal-600 hover:text-teal-800 mb-6 inline-block">
        ← Back to Games
      </Link>

      {/* Game Header */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-8">
        <div className="flex justify-between items-center mb-4">
          <div>
            <div className="text-sm text-gray-500 mb-2">
              {new Date(game.game_date_utc).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </div>
            <h1 className="text-3xl font-bold">
              {game.away_team} @ {game.home_team}
            </h1>
          </div>
          <div className="text-5xl font-bold text-teal-600">
            {game.away_score} - {game.home_score}
          </div>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <span className={`px-3 py-1 rounded-full ${
            game.status === 'FINAL' ? 'bg-gray-100 text-gray-800' : 'bg-blue-100 text-blue-800'
          }`}>
            {game.status}
          </span>
          {hasVideos && (
            <span className="px-3 py-1 rounded-full bg-green-100 text-green-800">
              ✓ Videos Available
            </span>
          )}
        </div>
      </div>

      {/* AI Recap Section */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
        <div className="bg-purple-600 text-white px-6 py-3 flex items-center gap-2">
          <span className="text-2xl">✍️</span>
          <h2 className="text-xl font-bold">AI Game Recap</h2>
        </div>
        <div className="p-6">
          {recap ? (
            <div>
              <p className="text-lg font-semibold text-gray-800 mb-4 italic">
                {recap.summary_line}
              </p>
              {recap.recap_text.split('\n\n').map((paragraph, i) => (
                <p key={i} className="text-gray-700 mb-3 leading-relaxed">
                  {paragraph}
                </p>
              ))}
            </div>
          ) : (
            <div className="text-center py-4">
              {recapError && (
                <p className="text-red-600 mb-4">{recapError}</p>
              )}
              <button
                onClick={generateRecap}
                disabled={recapLoading}
                className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {recapLoading ? 'Generating recap...' : 'Generate AI Recap'}
              </button>
              <p className="text-gray-500 text-sm mt-2">
                Powered by Claude AI
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Reddit Sentiment Section */}
      {sentiment && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
          <div className="bg-orange-500 text-white px-6 py-3 flex items-center gap-2">
            <span className="text-2xl">💬</span>
            <h2 className="text-xl font-bold">Fan Sentiment</h2>
            <span className="ml-auto text-sm opacity-80">r/SanJoseSharks</span>
          </div>
          <div className="p-6">
            {/* Mood and Summary */}
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">
                {sentiment.fan_mood === 'ecstatic' || sentiment.fan_mood === 'elated' ? '🎉' :
                 sentiment.fan_mood === 'impressed' || sentiment.fan_mood === 'hopeful' ? '😊' :
                 sentiment.fan_mood === 'frustrated' || sentiment.fan_mood === 'disappointed' ? '😤' :
                 sentiment.fan_mood === 'devastated' || sentiment.fan_mood === 'angry' ? '😡' : '😐'}
              </span>
              <div>
                <span className="text-lg font-semibold capitalize">{sentiment.fan_mood}</span>
                {sentiment.comment_count > 0 && (
                  <span className="text-gray-500 text-sm ml-2">({sentiment.comment_count} comments)</span>
                )}
              </div>
            </div>
            <p className="text-gray-700 mb-4">{sentiment.summary}</p>

            {/* Sentiment Bar */}
            <div className="flex h-4 rounded-full overflow-hidden mb-4">
              <div className="bg-green-500" style={{ width: `${(sentiment.positive_pct * 100)}%` }} />
              <div className="bg-gray-300" style={{ width: `${(sentiment.neutral_pct * 100)}%` }} />
              <div className="bg-red-500" style={{ width: `${(sentiment.negative_pct * 100)}%` }} />
            </div>
            <div className="flex justify-between text-sm text-gray-600 mb-4">
              <span className="text-green-600">{Math.round(sentiment.positive_pct * 100)}% Positive</span>
              <span>{Math.round(sentiment.neutral_pct * 100)}% Neutral</span>
              <span className="text-red-600">{Math.round(sentiment.negative_pct * 100)}% Negative</span>
            </div>

            {/* Themes */}
            {sentiment.top_themes?.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-500 mb-2">Top Themes</h3>
                <div className="flex flex-wrap gap-2">
                  {sentiment.top_themes.map((theme: string, i: number) => (
                    <span key={i} className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-700">
                      {theme}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Sample Quotes */}
            {(sentiment.sample_positive?.length > 0 || sentiment.sample_negative?.length > 0) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                {sentiment.sample_positive?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-green-600 mb-2">Positive Takes</h3>
                    {sentiment.sample_positive.map((q: string, i: number) => (
                      <p key={i} className="text-sm text-gray-600 italic mb-1">&ldquo;{q}&rdquo;</p>
                    ))}
                  </div>
                )}
                {sentiment.sample_negative?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-red-600 mb-2">Critical Takes</h3>
                    {sentiment.sample_negative.map((q: string, i: number) => (
                      <p key={i} className="text-sm text-gray-600 italic mb-1">&ldquo;{q}&rdquo;</p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Reddit Link */}
            {sentiment.thread_url && (
              <a
                href={sentiment.thread_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block mt-4 text-sm text-orange-600 hover:text-orange-800"
              >
                View full discussion on Reddit →
              </a>
            )}
          </div>
        </div>
      )}

      {/* Reddit Comments Section */}
      {(redditLoading || redditComments.length > 0) && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
          <div className="bg-orange-600 text-white px-6 py-3 flex items-center gap-2">
            <span className="text-2xl">📝</span>
            <h2 className="text-xl font-bold">Reddit Game Thread</h2>
            <span className="ml-auto text-sm opacity-80">r/SanJoseSharks</span>
          </div>
          <div className="p-6">
            {redditLoading ? (
              <p className="text-gray-500 text-center py-4">Loading comments...</p>
            ) : (
              <>
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  {redditComments.map((comment: any, i: number) => (
                    <div key={i} className="border-b border-gray-100 pb-3 last:border-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-gray-800">
                          {comment.author}
                        </span>
                        <span className="text-xs text-orange-600 font-medium">
                          {comment.score} pts
                        </span>
                        {comment.created_utc && (
                          <span className="text-xs text-gray-400">
                            {new Date(comment.created_utc * 1000).toLocaleString('en-US', {
                              month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
                            })}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 whitespace-pre-line">
                        {comment.body}
                      </p>
                    </div>
                  ))}
                </div>
                {redditThreadUrl && (
                  <a
                    href={redditThreadUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-4 text-sm text-orange-600 hover:text-orange-800"
                  >
                    View full thread on Reddit →
                  </a>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Video Section */}
      {hasVideos ? (
        <div className="space-y-8">
          {game.nhl_video_id && (
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="bg-red-600 text-white px-6 py-3 flex items-center gap-2">
                <span className="text-2xl">🎥</span>
                <h2 className="text-xl font-bold">NHL Official Recap</h2>
              </div>
              <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
                <iframe
                  className="absolute top-0 left-0 w-full h-full"
                  src={`https://www.youtube.com/embed/${game.nhl_video_id}`}
                  title="NHL Official Recap"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            </div>
          )}

          {game.professor_hockey_video_id && (
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="bg-blue-600 text-white px-6 py-3 flex items-center gap-2">
                <span className="text-2xl">📚</span>
                <h2 className="text-xl font-bold">Professor Hockey Analysis</h2>
              </div>
              <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
                <iframe
                  className="absolute top-0 left-0 w-full h-full"
                  src={`https://www.youtube.com/embed/${game.professor_hockey_video_id}`}
                  title="Professor Hockey Analysis"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
          <div className="text-4xl mb-4">⏳</div>
          <h3 className="text-xl font-semibold mb-2">Videos Processing</h3>
          <p className="text-gray-600">
            Game videos are being fetched. Check back in a few hours after the game ends!
          </p>
        </div>
      )}
    </main>
  );
}
