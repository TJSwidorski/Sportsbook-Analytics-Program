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
        for index, string in enumerate(data):
          if '%' in string:
            i = index
            next_score = [data[i + 3], data[i + 4]]
            data = data[i + 5:]
            scores.remove(['0', '0'])
            scores.append(next_score)
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

  def _sequential_clean_scores(self, scores_data) -> list:
    """
    Alternative score parser for sports whose scores_data embeds team or
    pitcher names (MLS, WNBA, CFL, MLB).

    Strategy:
      1. Filter to purely numeric tokens, discarding headers, team names,
         pitcher names, and no-data markers ('--', '-').
      2. Walk the token list, skipping concatenated score strings
         (e.g. '2133' that equals the next two tokens '21'+'33').
      3. Collect the remaining tokens as [away, home] pairs.
    """
    tokens = [t for t in scores_data if t.isdigit()]

    scores = []
    i = 0
    while i < len(tokens):
      # Detect a concatenated score: token == next_token + following_token
      if (i + 2 < len(tokens) and tokens[i] == tokens[i + 1] + tokens[i + 2]):
        i += 1  # skip the concat; the two components follow
        continue
      if i + 1 < len(tokens):
        scores.append([tokens[i], tokens[i + 1]])
        i += 2
      else:
        break

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
  and the scores data. Scores are parsed with _sequential_clean_scores to
  skip pitcher name tokens and concatenated score strings.
  """
  def clean_scores(self, scores_data):
    return self._sequential_clean_scores(scores_data)


class MLSMoneyLineAPI(MoneyLineAPI):
  """
  Money line parser for MLS (soccer).

  Team names are embedded in scores_data. Draws (0-0, 1-1, etc.) produce
  None/None W/L, handled correctly by Package downstream.
  """
  def clean_scores(self, scores_data):
    return self._sequential_clean_scores(scores_data)


class NCAAFMoneyLineAPI(MoneyLineAPI):
  """Money line parser for NCAAF. Week-based, no player names."""
  pass


class NCAABMoneyLineAPI(MoneyLineAPI):
  """Money line parser for NCAAB. Date-based, no player names."""
  pass


class WNBAMoneyLineAPI(MoneyLineAPI):
  """
  Money line parser for WNBA.

  Team names (e.g. 'Indiana', 'New York') are embedded in scores_data.
  """
  def clean_scores(self, scores_data):
    return self._sequential_clean_scores(scores_data)


class CFLMoneyLineAPI(MoneyLineAPI):
  """
  Money line parser for CFL.

  Team names are embedded in scores_data; the default week-based indices
  [3, 4] land on a score and a team name respectively. _sequential_clean_scores
  handles this by ignoring all non-numeric tokens.
  """
  def clean_scores(self, scores_data):
    return self._sequential_clean_scores(scores_data)


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

    self.soup = self.get_soup()
    data = self.get_data()
    scores = self.get_scores()
    bet_data = bet_dict[self.bet_type](self.date_type, date, data, scores)
    self.df = bet_data.package()

  def get_soup(self):
    page = requests.get(self.url)
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
