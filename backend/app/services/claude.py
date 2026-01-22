"""Claude API service for generating game recaps and summaries."""

from typing import Dict, Optional
from app.config import settings

# Only import if API key is configured
if settings.CLAUDE_API_KEY:
    from anthropic import Anthropic
    client = Anthropic(api_key=settings.CLAUDE_API_KEY)
else:
    client = None


def generate_game_recap(
    game_data: Dict,
    goal_details: list[Dict],
    top_performers: list[Dict],
    reddit_sentiment: Optional[Dict] = None
) -> Dict[str, str]:
    """
    Generate a magazine-style game recap using Claude.

    Args:
        game_data: Dict with away_team, home_team, away_score, home_score, etc.
        goal_details: List of goals with scorer, time, period info
        top_performers: List of top players with their stats
        reddit_sentiment: Optional sentiment data from Reddit comments

    Returns:
        Dict with:
            - summary_line: One-sentence lead (e.g., "Couture's PP tally was the difference")
            - recap_text: Full magazine-style recap (3-4 paragraphs)
            - next_game_storyline: Preview line for next game
    """
    if not client:
        return {
            "summary_line": f"{game_data['home_team']} defeats {game_data['away_team']} {game_data['home_score']}-{game_data['away_score']}",
            "recap_text": "Game recap unavailable (Claude API not configured)",
            "next_game_storyline": None
        }

    # Build the prompt
    prompt = f"""You are a sports journalist writing a compelling game recap for San Jose Sharks fans.

**GAME DETAILS:**
- Teams: {game_data['away_team']} @ {game_data['home_team']}
- Final Score: {game_data['away_score']} - {game_data['home_score']}
- Date: {game_data.get('game_date', 'Recent game')}

**GOALS:**
{_format_goals_for_prompt(goal_details)}

**TOP PERFORMERS:**
{_format_performers_for_prompt(top_performers)}

**FAN SENTIMENT:**
{_format_sentiment_for_prompt(reddit_sentiment) if reddit_sentiment else "Not available"}

**TASK:**
Generate a magazine-style game recap with:

1. **summary_line**: A single compelling sentence that captures the key moment or narrative (max 100 chars)
   Examples:
   - "Couture's power-play tally breaks tie in third period thriller"
   - "Blackwood stands tall with 35 saves in shutout performance"
   - "Sharks erase two-goal deficit to stun Ducks in overtime"

2. **recap_text**: A 3-4 paragraph recap (250-350 words) that:
   - Starts with the outcome and key storyline
   - Details critical moments and turning points
   - Highlights standout performances
   - Includes fan perspective if sentiment data available
   - Ends with forward-looking context (standings, momentum, etc.)
   - Write in an engaging, narrative style - not just listing stats

3. **next_game_storyline**: One sentence preview/question for next game (if next opponent provided)

**OUTPUT FORMAT:**
Return a JSON object with these three keys. Keep the tone professional but energetic - this is for passionate Sharks fans!"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse the response (Claude will return JSON format)
        response_text = message.content[0].text

        # Try to extract JSON from response
        import json
        # Claude might wrap JSON in markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        result = json.loads(response_text)

        return {
            "summary_line": result.get("summary_line", "")[:200],  # Ensure max length
            "recap_text": result.get("recap_text", ""),
            "next_game_storyline": result.get("next_game_storyline")
        }

    except Exception as e:
        print(f"Error generating recap with Claude: {e}")
        # Fallback to basic template
        return {
            "summary_line": f"{game_data['home_team']} defeats {game_data['away_team']} {game_data['home_score']}-{game_data['away_score']}",
            "recap_text": _generate_fallback_recap(game_data, goal_details, top_performers),
            "next_game_storyline": None
        }


def _format_goals_for_prompt(goals: list[Dict]) -> str:
    """Format goal details for Claude prompt."""
    if not goals:
        return "No goals scored"

    lines = []
    for i, goal in enumerate(goals, 1):
        assists_str = ", ".join([a for a in goal.get("assists", []) if a])
        assists_text = f" (Assists: {assists_str})" if assists_str else ""
        strength = goal.get("strength", "ev").upper()
        lines.append(
            f"{i}. Period {goal['period']}, {goal['time']} - "
            f"{goal['scorer']} ({goal['team']}) [{strength}]{assists_text}"
        )
    return "\n".join(lines)


def _format_performers_for_prompt(performers: list[Dict]) -> str:
    """Format top performers for Claude prompt."""
    if not performers:
        return "No standout performances"

    lines = []
    for p in performers[:5]:  # Top 5 performers
        stats = []
        if p.get("goals"):
            stats.append(f"{p['goals']}G")
        if p.get("assists"):
            stats.append(f"{p['assists']}A")
        if p.get("saves"):
            stats.append(f"{p['saves']} saves")
        if p.get("save_percentage"):
            stats.append(f"{p['save_percentage']} SV%")

        stats_str = ", ".join(stats)
        lines.append(f"- {p['name']} ({p.get('position', 'F')}): {stats_str}")

    return "\n".join(lines)


def _format_sentiment_for_prompt(sentiment: Dict) -> str:
    """Format Reddit sentiment data for Claude prompt."""
    if not sentiment:
        return "Not available"

    positive = sentiment.get("positive", 0)
    negative = sentiment.get("negative", 0)
    neutral = sentiment.get("neutral", 0)
    total = positive + negative + neutral

    if total == 0:
        return "No fan comments available"

    pos_pct = (positive / total * 100) if total > 0 else 0
    neg_pct = (negative / total * 100) if total > 0 else 0

    mood = "very positive" if pos_pct > 60 else "positive" if pos_pct > 40 else "mixed" if pos_pct > 25 else "negative"

    sample_comments = sentiment.get("sample_comments", [])[:3]
    comments_text = "\n".join([f'  - "{c}"' for c in sample_comments]) if sample_comments else "No sample comments"

    return f"Overall: {mood} ({pos_pct:.0f}% positive, {neg_pct:.0f}% negative)\nSample comments:\n{comments_text}"


def _generate_fallback_recap(game_data: Dict, goals: list[Dict], performers: list[Dict]) -> str:
    """Generate a basic template recap if Claude fails."""
    winner = game_data["home_team"] if game_data["home_score"] > game_data["away_score"] else game_data["away_team"]
    loser = game_data["away_team"] if winner == game_data["home_team"] else game_data["home_team"]

    recap = f"The {winner} defeated the {loser} {max(game_data['home_score'], game_data['away_score'])}-"
    recap += f"{min(game_data['home_score'], game_data['away_score'])}. "

    if goals:
        recap += f"{goals[0]['scorer']} opened the scoring in the {goals[0]['period']} period. "

    if performers:
        top = performers[0]
        if top.get("goals"):
            recap += f"{top['name']} led the way with {top['goals']} goals. "
        elif top.get("saves"):
            recap += f"{top['name']} was solid in net with {top['saves']} saves. "

    return recap