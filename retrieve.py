import time
import requests
from bs4 import BeautifulSoup
import pandas as pd


class MoneyLineAPI():
  """
  Base class for retrieving money line data from SportsBook Review.
  Handles sports where raw odds data contains no embedded player names.
  Sport-specific subclasses override _is_player_name() when needed.
  """
  # Default score start indices keyed by date type (NBA/NFL/NHL/NCAAB baseline).
  # Subclasses may override _scores_indices to point to different positions
  # when their HTML structure differs.
  _scores_indices = {
    'Week': [3, 4],
    'Date': [2, 3],
  }

  def __init__(self, date_type: str, date, data, scores):
    self.date_type = date_type.lower().capitalize()
    indices = self.__class__._scores_indices
    # Support either a dict keyed by date type or a direct [first, second] list
    self.scores_indices = indices[self.date_type] if isinstance(indices, dict) else indices
    self.date = "Week " + str(date) if isinstance(date, int) else date
    self.data = self.clean_data(data)
    self.scores = self.clean_scores(scores)

  def _is_odds(self, text: str) -> bool:
    """Return True if text is a valid American odds string (+110, -220, etc.)."""
    if len(text) < 2 or text[0] not in ('+', '-'):
      return False
    return text[1:].isdigit()

  def _is_time(self, text: str) -> bool:
    return 'AM' in text or 'PM' in text

  def _is_player_name(self, text: str) -> bool:
    """
    Return True if text looks like a player/starter name that should be
    skipped. Base implementation always returns False; overridden by
    sport-specific subclasses that embed names in their raw data.
    """
    return False

  def clean_data(self, data):
    """
    Given raw-data [data], return a list of games where each game is a
    dictionary containing: date_type key, 'Away Lines', and 'Home Lines'.
    """
    games = []
    game_info = {}
    index = 0

    while index < len(data):
      token = data[index]
      if self._is_time(token):
        if game_info:
          games.append(game_info)
        game_info = {self.date_type: self.date, 'Lines': []}
      elif token == '-':
        index += 1
        continue
      elif self._is_player_name(token):
        pass
      elif self._is_odds(token):
        if game_info:
          game_info['Lines'].append(token)
      index += 1

    if game_info:
      games.append(game_info)

    for game in games:
      lines = game['Lines']
      game['Away Lines'] = [l for i, l in enumerate(lines) if i % 2 == 0]
      game['Home Lines'] = [l for i, l in enumerate(lines) if i % 2 != 0]
      del game['Lines']

    return games

  def find(self, element, data):
    """
    Find the first index i where [data[i], data[i+1]] == element.
    Returns None if not found.
    """
    ele_len = len(element)
    data_len = len(data)
    i = 0
    while i < (data_len - ele_len):
      if [str(data[i]), str(data[i + 1])] == element:
        return i
      i += 1
    return None

  def clean_scores(self, scores_data):
    """
    Given raw-data [scores_data], return a list of [away_score, home_score]
    pairs for each game on the given date.
    """
    first_index = self.scores_indices[0]
    second_index = self.scores_indices[1]
    scores = []
    game_index = 0
    first_score = [scores_data[first_index], scores_data[second_index]]
    data = scores_data[second_index + 1:]
    scores.append(first_score)

    while True:
      if scores[game_index] == ['0', '0']:
        found = False
        for index, string in enumerate(data):
          if '%' in string:
            i = index
            next_score = [data[i + 3], data[i + 4]]
            data = data[i + 5:]
            scores.remove(['0', '0'])
            scores.append(next_score)
            found = True
            break
        if not found:
          # No '%' marker left — remaining games are unplayed. Drop the
          # placeholder and stop; downstream dropna() handles short scores.
          scores.remove(['0', '0'])
          break
        continue

      i = self.find(scores[game_index], data)
      if (i is not None) and (('%' in data[i + 2]) or ('-' in data[i + 2])):
        if len(data) > 3:
          i += 4
          if (i + 3) > len(data):
            break
          else:
            next_score = [data[i + 1], data[i + 2]]
            data = data[i + 3:]
            scores.append(next_score)
            game_index += 1
        else:
          break
      elif i is not None:
        data = data[i + 1:]
      else:
        print("Score causing error:", scores)
        print("Data:", data)
        raise ValueError(self.date)

    return scores

  def package(self):
    """
    Combine cleaned line data and scores into a single DataFrame.
    """
    df = pd.DataFrame(self.data, columns=[self.date_type, 'Away Lines', 'Home Lines'])
    scores_df = pd.DataFrame(self.scores, columns=['Away Score', 'Home Score'])
    df.reset_index(drop=True, inplace=True)
    scores_df.reset_index(drop=True, inplace=True)
    return pd.concat([df, scores_df], axis=1)


class _PlayerNameMixin:
  """
  Mixin that filters embedded player/starter names from raw money-line data.
  Applied to sports where SportsBook Review includes names (e.g., NHL goalies,
  MLB pitchers) inline with the odds strings.

  Detection: names contain only letters, spaces, hyphens, apostrophes, or
  periods and are not valid odds strings or time markers.
  """
  def _is_player_name(self, text: str) -> bool:
    if self._is_time(text) or self._is_odds(text) or text == '-':
      return False
    clean = text.replace('-', '').replace("'", '').replace('.', '').replace(' ', '')
    return clean.isalpha() and len(text) > 2


# ---------------------------------------------------------------------------
# Sport-specific MoneyLineAPI subclasses
# ---------------------------------------------------------------------------

class NBAMoneyLineAPI(MoneyLineAPI):
  """Money line parser for NBA. No player names in raw data."""
  pass


class NFLMoneyLineAPI(MoneyLineAPI):
  """Money line parser for NFL. No player names in raw data."""
  pass


class NHLMoneyLineAPI(_PlayerNameMixin, MoneyLineAPI):
  """
  Money line parser for NHL.

  Older SportsBook Review NHL data embedded starting goalie names inline with
  odds. Later data dropped goalies. This parser always filters name-like tokens
  so it handles both eras without configuration.
  """
  pass


class MLBMoneyLineAPI(_PlayerNameMixin, MoneyLineAPI):
  """
  Money line parser for MLB.

  Pitcher names appear in both the odds data (filtered by _PlayerNameMixin)
  and the scores data. Each game's score block ends with a betting-percentage
  marker (e.g. '56%44%') which anchors the recap totals.
  """
  def clean_scores(self, scores_data):
    """
    Parse MLB score totals by anchoring on the concatenated betting-%
    marker that closes each game's row. Per-game token layout from SBR:

      AwayPitcher(L|R)  AwayTotal
      HomePitcher(L|R)  HomeTotal
      [InningConcat I_a I_h] × 9 innings
      AwayRecap  HomeRecap          ← what we want
      'XX%YY%'  'XX%'  'YY%'

    The two numeric tokens immediately preceding the 'XX%YY%' marker are
    the recap totals for that game. Games still in progress or postponed
    have no marker and are simply skipped (downstream dropna handles the
    short scores frame).
    """
    scores = []
    for i, token in enumerate(scores_data):
      if token.count('%') != 2 or i < 2:
        continue
      away = scores_data[i - 2]
      home = scores_data[i - 1]
      if away.isdigit() and home.isdigit():
        scores.append([away, home])
    return scores


class MLSMoneyLineAPI(MoneyLineAPI):
  """Money line parser for MLS (soccer). Score parser: TODO."""
  def clean_scores(self, scores_data):
    return []


class NCAAFMoneyLineAPI(MoneyLineAPI):
  """Money line parser for NCAAF. Week-based, no player names."""
  pass


class NCAABMoneyLineAPI(MoneyLineAPI):
  """Money line parser for NCAAB. Date-based, no player names."""
  pass


class WNBAMoneyLineAPI(MoneyLineAPI):
  """Money line parser for WNBA. Score parser: TODO."""
  def clean_scores(self, scores_data):
    return []


class CFLMoneyLineAPI(MoneyLineAPI):
  """Money line parser for CFL. Score parser: TODO."""
  def clean_scores(self, scores_data):
    return []


# ---------------------------------------------------------------------------
# Maps sport name → MoneyLineAPI subclass for SportsbookReviewAPI dispatch
# ---------------------------------------------------------------------------

_SPORT_MONEYLINE_MAP = {
  'nba':   NBAMoneyLineAPI,
  'nfl':   NFLMoneyLineAPI,
  'nhl':   NHLMoneyLineAPI,
  'mlb':   MLBMoneyLineAPI,
  'mls':   MLSMoneyLineAPI,
  'ncaaf': NCAAFMoneyLineAPI,
  'ncaab': NCAABMoneyLineAPI,
  'wnba':  WNBAMoneyLineAPI,
  'cfl':   CFLMoneyLineAPI,
}


class PointSpreadAPI():
  pass


class TotalsAPI():
  pass


class SportsbookReviewAPI():
  """
  Fetches and parses a SportsBook Review page for a given sport and bet type.

  Parameters
  ----------
  url       : Full SportsBook Review URL for the desired page.
  bet_type  : 'Money Line', 'Point Spread', or 'Totals'.
  date_type : 'Week' for week-based sports (NFL, NCAAF, CFL) or 'Date' for
              all others.
  date      : Week number (int) or date string 'YYYY-MM-DD'.
  sport     : Sport identifier — one of 'nba', 'nfl', 'nhl', 'mlb', 'mls',
              'ncaaf', 'ncaab', 'wnba', 'cfl'. Determines the cleaning
              algorithm used for the raw HTML data.
  """
  def __init__(self, url: str, bet_type: str, date_type: str, date, sport: str):
    self.url = url
    self.bet_type = bet_type.lower()
    self.date_type = date_type.lower()
    self.sport = sport.lower()

    if self.sport not in _SPORT_MONEYLINE_MAP:
      raise ValueError(
        f"Unknown sport '{self.sport}'. Valid options: {sorted(_SPORT_MONEYLINE_MAP)}"
      )

    bet_dict = {
      'money line': _SPORT_MONEYLINE_MAP[self.sport],
      'point spread': PointSpreadAPI,
      'totals': TotalsAPI,
    }

    tag = f"[sbr-trace {self.sport}/{date}]"
    t0 = time.perf_counter()
    def _mark(stage: str):
      print(f"{tag} {stage} t+{time.perf_counter() - t0:.2f}s", flush=True)

    _mark("BEGIN get_soup")
    self.soup = self.get_soup()
    _mark("END   get_soup")

    _mark("BEGIN get_data")
    data = self.get_data()
    _mark(f"END   get_data (tokens={len(data)})")

    _mark("BEGIN get_scores")
    scores = self.get_scores()
    _mark(f"END   get_scores (tokens={len(scores)})")

    _mark("BEGIN MoneyLineAPI.__init__ (clean_data + clean_scores)")
    bet_data = bet_dict[self.bet_type](self.date_type, date, data, scores)
    _mark("END   MoneyLineAPI.__init__")

    _mark("BEGIN package")
    self.df = bet_data.package()
    _mark("END   package")

  def get_soup(self):
    # SBR blocks the default python-requests UA (hangs indefinitely), so we
    # masquerade as a browser. Timeout guards against network stalls.
    headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36',
    }
    page = requests.get(self.url, headers=headers, timeout=20)
    if page.status_code == 200:
      return BeautifulSoup(page.text, 'html.parser')
    raise FileNotFoundError(f"Unable to access URL: {self.url}")

  def get_data(self):
    data = []
    for span in self.soup.find_all('span', class_='fs-9'):
      text = span.get_text(strip=True)
      if text:
        data.append(text)
    return data

  def get_scores(self):
    scores = []
    for div in self.soup.find_all('div', class_='fs-9'):
      text = div.get_text(strip=True)
      if text:
        scores.append(text)
    return scores

  def return_data(self) -> pd.DataFrame:
    return self.df
