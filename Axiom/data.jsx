// Shared mock data for all three directions.

const TODAYS_GAMES = [
  { league: "NBA", away: "Boston Celtics", home: "Denver Nuggets", awayAbbr: "BOS", homeAbbr: "DEN", time: "7:30 PM ET", pick: "DEN -3.5", confidence: 84, edge: "+4.1%", market: "Spread", line: "-3.5", units: 2.5 },
  { league: "NFL", away: "Kansas City", home: "Buffalo", awayAbbr: "KC", homeAbbr: "BUF", time: "8:20 PM ET", pick: "Over 47.5", confidence: 71, edge: "+2.8%", market: "Total", line: "O 47.5", units: 1.5 },
  { league: "MLB", away: "LA Dodgers", home: "Atlanta", awayAbbr: "LAD", homeAbbr: "ATL", time: "7:05 PM ET", pick: "LAD ML", confidence: 66, edge: "+3.4%", market: "Moneyline", line: "-128", units: 1.0 },
  { league: "NHL", away: "Edmonton", home: "Florida", awayAbbr: "EDM", homeAbbr: "FLA", time: "7:00 PM ET", pick: "Under 6.5", confidence: 78, edge: "+5.2%", market: "Total", line: "U 6.5", units: 2.0 },
  { league: "NCAAF", away: "Michigan", home: "Ohio State", awayAbbr: "MICH", homeAbbr: "OSU", time: "12:00 PM ET", pick: "MICH +6.5", confidence: 73, edge: "+3.9%", market: "Spread", line: "+6.5", units: 1.5 },
  { league: "NCAAB", away: "Duke", home: "UNC", awayAbbr: "DUKE", homeAbbr: "UNC", time: "9:00 PM ET", pick: "UNC ML", confidence: 69, edge: "+2.6%", market: "Moneyline", line: "-145", units: 1.0 },
  { league: "EPL", away: "Arsenal", home: "Man City", awayAbbr: "ARS", homeAbbr: "MCI", time: "10:00 AM ET", pick: "Over 2.5", confidence: 76, edge: "+4.4%", market: "Total", line: "O 2.5", units: 2.0 },
  { league: "NBA", away: "LA Lakers", home: "Phoenix", awayAbbr: "LAL", homeAbbr: "PHX", time: "10:00 PM ET", pick: "PHX -2", confidence: 64, edge: "+2.1%", market: "Spread", line: "-2", units: 1.0 },
];

// Last 30 days of cumulative units, slightly noisy upward
const PERFORMANCE_30D = (() => {
  const arr = [];
  let v = 0;
  for (let i = 0; i < 30; i++) {
    const drift = 0.55;
    const noise = (Math.random() - 0.45) * 3;
    v += drift + noise;
    arr.push({ day: i + 1, units: +v.toFixed(2) });
  }
  return arr;
})();

const RECENT_PICKS = [
  { date: "Apr 27", league: "NBA", matchup: "BOS @ MIA", pick: "MIA +4.5", result: "W", units: "+1.5" },
  { date: "Apr 27", league: "MLB", matchup: "NYY @ TOR", pick: "Under 8.5", result: "W", units: "+2.0" },
  { date: "Apr 26", league: "NHL", matchup: "TOR @ BOS", pick: "BOS ML", result: "W", units: "+1.0" },
  { date: "Apr 26", league: "NBA", matchup: "DEN @ MIN", pick: "DEN -3", result: "L", units: "-2.5" },
  { date: "Apr 25", league: "EPL", matchup: "LIV vs CHE", pick: "Over 2.5", result: "W", units: "+1.5" },
  { date: "Apr 25", league: "NBA", matchup: "OKC @ DAL", pick: "OKC -1.5", result: "W", units: "+2.0" },
  { date: "Apr 24", league: "NFL", matchup: "Draft prop", pick: "Under 4.5 QBs", result: "W", units: "+3.0" },
  { date: "Apr 24", league: "MLB", matchup: "ATL @ PHI", pick: "ATL ML", result: "L", units: "-1.0" },
  { date: "Apr 23", league: "NBA", matchup: "GSW @ HOU", pick: "Over 224.5", result: "W", units: "+1.0" },
  { date: "Apr 23", league: "NHL", matchup: "EDM @ VAN", pick: "Under 6", result: "W", units: "+1.5" },
];

const SEASON_BACKTEST = [
  { season: "2019-20", picks: 1842, winRate: 58.4, units: 42.6, roi: 11.8, sport: "All" },
  { season: "2020-21", picks: 2104, winRate: 61.2, units: 58.1, roi: 14.3, sport: "All" },
  { season: "2021-22", picks: 2287, winRate: 62.8, units: 67.4, roi: 15.6, sport: "All" },
  { season: "2022-23", picks: 2398, winRate: 63.5, units: 71.2, roi: 16.1, sport: "All" },
  { season: "2023-24", picks: 2541, winRate: 64.7, units: 78.3, roi: 17.4, sport: "All" },
  { season: "2024-25", picks: 1984, winRate: 65.1, units: 71.0, roi: 18.2, sport: "All" },
];

const SPORT_BREAKDOWN = [
  { sport: "NBA", picks: 2840, winRate: 66.2, units: 92.4 },
  { sport: "NFL", picks: 612, winRate: 64.8, units: 31.7 },
  { sport: "MLB", picks: 3120, winRate: 63.1, units: 84.2 },
  { sport: "NHL", picks: 1820, winRate: 65.4, units: 54.8 },
  { sport: "NCAAF", picks: 480, winRate: 67.3, units: 28.9 },
  { sport: "NCAAB", picks: 1240, winRate: 64.9, units: 41.6 },
  { sport: "EPL", picks: 1044, winRate: 62.7, units: 32.4 },
];

window.TODAYS_GAMES = TODAYS_GAMES;
window.PERFORMANCE_30D = PERFORMANCE_30D;
window.RECENT_PICKS = RECENT_PICKS;
window.SEASON_BACKTEST = SEASON_BACKTEST;
window.SPORT_BREAKDOWN = SPORT_BREAKDOWN;
