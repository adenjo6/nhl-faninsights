import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Link from "next/link";

type GameDetail = {
  game_id: number;
  away_team: string;
  home_team: string;
  away_score: number;
  home_score: number;
  game_date: string;
  nhl_video_id?: string;
  professor_hockey_video_id?: string;
  status: string;
};

export default function GamePage() {
  const router = useRouter();
  const { gameId } = router.query;
  const [game, setGame] = useState<GameDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
              {new Date(game.game_date).toLocaleDateString('en-US', {
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
