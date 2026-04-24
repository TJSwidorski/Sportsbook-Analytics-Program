class BetTypes():
  """
  Creates the links for each bet type for the Sportsbook Review website.
  """
  def __init__(self, base_url: str, date_type: str):
    """
    Creates the Sportsbook Review urls for spread, money line, and totals given
    the sport-specific base url [base_url] and the date or week [date_type].
    """
    self.spread = str(base_url.rsplit('/', 1)[0]) + '/pointspread/full-game/' + str(base_url.rsplit('/', 1)[1]) + date_type
    self.money_line = str(base_url.rsplit('/', 1)[0]) + '/money-line/full-game/' + str(base_url.rsplit('/', 1)[1]) + date_type
    self.totals = str(base_url.rsplit('/', 1)[0]) + '/totals/full-game/' + str(base_url.rsplit('/', 1)[1]) + date_type

  def quarters(self, quarter_num: int):
    """
    Given the initialized full game links, creates the bet links for the 
    quarter [quarter_num]. 
    """
    #Quarters need both the bet type indicators and the quarter
    if quarter_num == 1:
      quarter = "1st"
    elif quarter_num == 2:
      quarter = "2nd"
    elif quarter_num == 3:
      quarter = "3rd"
    elif quarter_num == 4:
      quarter = "4th"
    else:
      print("Invalid quarter number:", quarter_num)
    
    spread = self.spread.replace('full-game', quarter + '-quarter')
    money_line = self.money_line.replace('full-game', quarter + '-quarter')
    totals = self.totals.replace('full-game', quarter + '-quarter')

    return spread, money_line, totals
  
  def halves(self, half_num: int):
    """
    Given the initialized full game links, creates the bet links for the 
    half [half_num].
    """
    if half_num == 1:
      half = "1st"
    elif half_num == 2:
      half = "2nd"
    else:
      print("Invalid half number:", half_num)

    spread = self.spread.replace('full-game', half + '-half')
    money_line = self.money_line.replace('full-game', half + '-half')
    totals = self.totals.replace('full-game', half + '-half')

    return spread, money_line, totals

class NFL():
  """
  The base class for NFL data.
  """
  def __init__(self, week_num):
    """
    Creates the links for each bet type and time type for the NFL.
    """
    #Set week as a string
    if type(week_num) == int:
      self.__week = "Week" + str(week_num)
    elif type(week_num) == str:
      self.__week = week_num
    #Initialize the base url
    self.__base_url = "https://www.sportsbookreview.com/betting-odds/nfl-football/?week="
    #Create the base links
    self.links = BetTypes(self.__base_url, self.__week)
    #Set full-game spread link
    self.spread = self.links.spread
    #Set full-game money line link
    self.money_line = self.links.money_line
    #Set full-game totals link
    self.totals = self.links.totals
    #Initialize quarters links
    self.quarters()
    #Initialize halves links
    self.halves()

  def quarters(self):
    """
    Creates the links for each quarter bet types for the NFL.
    """
    self.q1_spread, self.q1_money_line, self.q1_totals = self.links.quarters(1)
    self.q2_spread, self.q2_money_line, self.q2_totals = self.links.quarters(2)
    self.q3_spread, self.q3_money_line, self.q3_totals = self.links.quarters(3)
    self.q4_spread, self.q4_money_line, self.q4_totals = self.links.quarters(4)

  def halves(self):
    """
    Creates the links for each half bet types for the NFL.
    """
    self.h1_spread, self.h1_money_line, self.h1_totals = self.links.halves(1)
    self.h2_spread, self.h2_money_line, self.h2_totals = self.links.halves(2)

class NBA():
  """
  The base class for NBA data.
  """
  def __init__(self, date: str):
    """
    Creates the links for each bet type and time type for the NFL.
    """
    self.__date = date
    self.__base_url = "https://www.sportsbookreview.com/betting-odds/nba-basketball/?date="
    self.links = BetTypes(self.__base_url, self.__date)
    self.spread = self.links.spread
    self.money_line = self.links.money_line
    self.totals = self.links.totals
    self.quarters()
    self.halves()

  def quarters(self):
    """
    Creates the links for each quarter bet types for the NBA.
    """
    self.q1_spread, self.q1_money_line, self.q1_totals = self.links.quarters(1)
    self.q2_spread, self.q2_money_line, self.q2_totals = self.links.quarters(2)
    self.q3_spread, self.q3_money_line, self.q3_totals = self.links.quarters(3)
    self.q4_spread, self.q4_money_line, self.q4_totals = self.links.quarters(4)

  def halves(self):
    """
    Creates the links for each half bet types for the NBA.
    """
    self.h1_spread, self.h1_money_line, self.h1_totals = self.links.halves(1)
    self.h2_spread, self.h2_money_line, self.h2_totals = self.links.halves(2)

class NHL():
  """
  The base class for NHL data.
  """
  def __init__(self, date: str):
    """
    Creates the links for each bet type and time type for the NHL.
    """
    self.__date = date
    self.__base_url = "https://www.sportsbookreview.com/betting-odds/nhl-hockey/?date="
    self.links = BetTypes(self.__base_url, self.__date)
    self.spread = self.links.spread
    self.money_line = self.links.money_line
    self.totals = self.links.totals
    self.periods()

  def periods(self):
    """
    Creates the links for each period bet types for the NHL.
    """
    #Sportsbook Review names the periods as 'quarters'.
    self.p1_spread, self.p1_money_line, self.p1_totals = self.links.quarters(1)
    self.p2_spread, self.p2_money_line, self.p2_totals = self.links.quarters(2)
    self.p3_spread, self.p3_money_line, self.p3_totals = self.links.quarters(3)

class MLB():
  """
  The base class for MLB data.
  """
  def __init__(self, date: str):
    """
    Creates the links for each bet type and time type for the MLB.
    """
    self.__date = date
    self.__base_url = "https://www.sportsbookreview.com/betting-odds/mlb-baseball/?date="
    self.links = BetTypes(self.__base_url, self.__date)
    self.spread = self.links.spread
    self.money_line = self.links.money_line
    self.totals = self.links.totals
    self.innings()

  def innings(self):
    """
    Creates the links for the first 5 innings for the MLB.
    """
    self.i1_spread, self.i1_money_line, self.i1_totals = self.links.halves(1)

class MLS():
  """
  The base class for MLS data.
  """
  def __init__(self, date: str):
    """
    Creates the links for each bet type and time type for the MLS.
    """
    self.__date = date
    self.__base_url = "https://www.sportsbookreview.com/betting-odds/major-league-soccer/?date="
    self.links = BetTypes(self.__base_url, self.__date)
    self.spread = self.links.spread
    self.money_line = self.links.money_line
    self.totals = self.links.totals

class NCAAF():
  """
  The base class for NCAAF data.
  """
  def __init__(self, week_num: int):
    """
    Creates the links for each bet type and time type for NCAAF.
    """
    self.__week = str(week_num)
    self.__base_url = "https://www.sportsbookreview.com/betting-odds/college-football/?week=Week"
    self.links = BetTypes(self.__base_url, self.__week)
    self.spread = self.links.spread
    self.money_line = self.links.money_line
    self.totals = self.links.totals
    self.quarters()
    self.halves()

  def quarters(self):
    """
    Creates the links for the each quarter bet types for NCAAF.
    """
    self.q1_spread, self.q1_money_line, self.q1_totals = self.links.quarters(1)
    self.q2_spread, self.q2_money_line, self.q2_totals = self.links.quarters(2)
    self.q3_spread, self.q3_money_line, self.q3_totals = self.links.quarters(3)
    self.q4_spread, self.q4_money_line, self.q4_totals = self.links.quarters(4)

  def halves(self):
    """
    Creates the links for each half bet types for NCAAF.
    """
    self.h1_spread, self.h1_money_line, self.h1_totals = self.links.halves(1)
    self.h2_spread, self.h2_money_line, self.h2_totals = self.links.halves(2)

class NCAAB():
  """
  The base class for NCAAB data.
  """
  def __init__(self, date: str):
    """
    Creates the links for each bet type and time type for NCAAB.
    """
    self.__date = date
    self.__base_url = "https://www.sportsbookreview.com/betting-odds/ncaa-basketball/?date="
    self.links = BetTypes(self.__base_url, self.__date)
    self.spread = self.links.spread
    self.money_line = self.links.money_line
    self.totals = self.links.totals
    self.quarters()
    self.halves()

  def quarters(self):
    """
    Creates the links for each quarter bet types for NCAAB.
    """
    self.q1_spread, self.q1_money_line, self.q1_totals = self.links.quarters(1)
    self.q2_spread, self.q2_money_line, self.q2_totals = self.links.quarters(2)
    self.q3_spread, self.q3_money_line, self.q3_totals = self.links.quarters(3)
    self.q4_spread, self.q4_money_line, self.q4_totals = self.links.quarters(4)

  def halves(self):
    """
    Creates the links for each half bet types for NCAAB.
    """
    self.h1_spread, self.h1_money_line, self.h1_totals = self.links.halves(1)
    self.h2_spread, self.h2_money_line, self.h2_totals = self.links.halves(2)

class WNBA():
  """
  The base class for WNBA data.
  """
  def __init__(self, date: str):
    """
    Creates the links for each bet type and time type for the WNBA.
    """
    self.__date = date
    self.__base_url = "https://www.sportsbookreview.com/betting-odds/wnba-basketball/?date="
    self.links = BetTypes(self.__base_url, self.__date)
    self.spread = self.links.spread
    self.money_line = self.links.money_line
    self.totals = self.links.totals
    self.quarters()
    self.halves()

  def quarters(self):
    """
    Creates the links for each quarter bet types for the WNBA.
    """
    self.q1_spread, self.q1_money_line, self.q1_totals = self.links.quarters(1)
    self.q2_spread, self.q2_money_line, self.q2_totals = self.links.quarters(2)
    self.q3_spread, self.q3_money_line, self.q3_totals = self.links.quarters(3)
    self.q4_spread, self.q4_money_line, self.q4_totals = self.links.quarters(4)

  def halves(self):
    """
    Creates the links for each half bet types for the WNBA.
    """
    self.h1_spread, self.h1_money_line, self.h1_totals = self.links.halves(1)
    self.h2_spread, self.h2_money_line, self.h2_totals = self.links.halves(2)

class CFL():
  """
  The base class for CFL data.
  """
  def __init__(self, week_num: int):
    """
    Creates the links for each bet type and time type for the CFL.
    """
    self.__week = str(week_num)
    self.__base_url = "https://www.sportsbookreview.com/betting-odds/cfl-football/?week=Week"
    self.links = BetTypes(self.__base_url, self.__week)
    self.spread = self.links.spread
    self.money_line = self.links.money_line
    self.totals = self.links.totals
    self.quarters()
    self.halves()

  def quarters(self):
    """
    Creates the links for each quarter bet types for the CFL.
    """
    self.q1_spread, self.q1_money_line, self.q1_totals = self.links.quarters(1)
    self.q2_spread, self.q2_money_line, self.q2_totals = self.links.quarters(2)
    self.q3_spread, self.q3_money_line, self.q3_totals = self.links.quarters(3)
    self.q4_spread, self.q4_money_line, self.q4_totals = self.links.quarters(4)

  def halves(self):
    """
    Creates the links for each half bet types for the CFL.
    """
    self.h1_spread, self.h1_money_line, self.h1_totals = self.links.halves(1)
    self.h2_spread, self.h2_money_line, self.h2_totals = self.links.halves(2)
