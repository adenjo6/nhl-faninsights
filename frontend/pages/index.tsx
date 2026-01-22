import { useState, useEffect } from "react";
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

export default function Home() {
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    // Get recent completed games (default limit of 10 from backend)
    fetch(`${apiUrl}/api/games/recent`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to fetch games: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        setGames(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching games:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <main className="max-w-6xl mx-auto p-6">
        <h1 className="text-4xl font-bold mb-8 text-teal-600">🏒 NHL Fan Insights</h1>
        <p className="text-gray-600">Loading games...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="max-w-6xl mx-auto p-6">
        <h1 className="text-4xl font-bold mb-8 text-teal-600">🏒 NHL Fan Insights</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
          <p className="text-sm text-red-600 mt-2">
            Make sure the backend is running at {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
          </p>
        </div>
      </main>
    );
  }

  // All games are completed (filtered by backend)
  const displayedGames = games;

  return (
    <main className="max-w-6xl mx-auto p-6">
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-2 text-teal-600">🏒 NHL Fan Insights</h1>
        <p className="text-gray-600">San Jose Sharks Game Recaps with Video Highlights</p>
      </header>

      {displayedGames.length === 0 ? (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-gray-600">
            No completed games yet. Check back after the first Sharks game!
          </p>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {displayedGames.map((game) => (
            <Link
              key={game.game_id}
              href={`/game/${game.game_id}`}
              className="block border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow bg-white"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="text-sm text-gray-500 mb-1">
                    {new Date(game.game_date).toLocaleDateString()}
                  </div>
                  <div className="font-bold text-lg">
                    {game.away_team} @ {game.home_team}
                  </div>
                </div>
                <div className="text-2xl font-bold text-teal-600">
                  {game.away_score} - {game.home_score}
                </div>
              </div>

              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <div className="flex items-center gap-2 text-sm">
                  {game.has_videos ? (
                    <>
                      <span className="text-green-600">✓</span>
                      <span className="text-green-600">Videos Available</span>
                    </>
                  ) : (
                    <>
                      <span className="text-gray-400">○</span>
                      <span className="text-gray-500">Processing...</span>
                    </>
                  )}
                </div>
                <span className="text-teal-600 font-medium">View →</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}