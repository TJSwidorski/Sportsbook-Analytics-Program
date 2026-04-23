import sports
import retrieve
import package
import pandas as pd
import bayes as nb
from datetime import datetime, timedelta

if __name__ == '__main__':
  # NHL Test
  print("NHL Season Data")
  df_list = []
  date = '2024-10-08'
  while date != '2025-02-08':
    try:
      nhl = sports.NHL(date)
      df = retrieve.SportsbookReviewAPI(nhl.money_line, 'Money Line', 'Date', date, sport='nhl').return_data()
      df_list.append(df)
      date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1))
      date = date.strftime('%Y-%m-%d')
    except:
      print("Error: Unable to retrieve data for date: " + date)
      date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1))
      date = date.strftime('%Y-%m-%d')

  df = pd.concat(df_list)
  print("Season Data:", df)
  season_data = package.Package(df, true_prob=False)
  away_season_data = season_data.return_away()
  print("Away Season Data:", away_season_data)
  home_season_data = season_data.return_home()
  print("Home Season Data:", home_season_data)

  print("Test Data")
  test_list = []
  date = "2025-02-08"
  while date != '2025-02-10':
    print("Date:", date)
    nhl = sports.NHL(date)
    test_df = retrieve.SportsbookReviewAPI(nhl.money_line, 'Money Line', 'Date', date, sport='nhl').return_data()
    print("Test Data:", test_df)
    for i in range(len(test_df)):
      print(f"Game {i+1}")
      ax = test_df['Away Lines'][i]
      away_nb = nb.NaiveBayes('Away', away_season_data)
      p_away = away_nb.probability(ax)
      print(f"P(Away): {p_away}")
      hx = test_df['Home Lines'][i]
      home_nb = nb.NaiveBayes('Home', home_season_data)
      p_home = home_nb.probability(hx)
      print(f"P(Home): {p_home}")

    date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1))
    date = date.strftime('%Y-%m-%d')
    
  # NFL Test
  #Package Multiple Weeks Together
  print("NFL Season 59 Information")
  df_list = []
  week = 1
  while week <= 18:
    try:
      nfl = sports.NFL(week)
      df = retrieve.SportsbookReviewAPI(nfl.money_line, 'Money Line', 'Week', week, sport='nfl').return_data()
      print("Week ", week)
      df_list.append(df)
      week += 1
    except:
      print("Error")
      week += 1

  df = pd.concat(df_list)
  print("Season Data:", df)
  season_data = package.Package(df, true_prob=False)
  away_season_data = season_data.return_away()
  print("Away Season Data:", away_season_data)
  home_season_data = season_data.return_home()
  print("Home Season Data:", home_season_data)

  print("Wild Card Week")
  week = "SuperBowl"
  nfl = sports.NFL(week)
  wildcard_df = retrieve.SportsbookReviewAPI(nfl.money_line, 'Money Line', 'Week', week, sport='nfl').return_data()
  print(wildcard_df)
  for i in range(len(wildcard_df)):
    print(f"Game {i+1}")
    ax = wildcard_df['Away Lines'][i]
    away_wildcard_nb = nb.NaiveBayes('Away', away_season_data)
    p_away = away_wildcard_nb.probability(ax)
    print(p_away)
    ah = wildcard_df['Home Lines'][i]
    home_wildcard_nb = nb.NaiveBayes('Home', home_season_data)
    p_home = home_wildcard_nb.probability(ah)
    print(p_home)