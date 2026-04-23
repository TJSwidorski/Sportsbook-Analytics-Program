import sports
import retrieve
import package
import pandas as pd
import bayes as bn
from datetime import datetime, timedelta

if __name__ == '__main__':
  #NFL Display
  print("NFL Display")
  week = 9
  nfl = sports.NFL(week)
  df = retrieve.SportsbookReviewAPI(nfl.money_line, 'Money Line', 'Week', week, sport='nfl').return_data()
  print(df)

  pack = package.Package(df, true_prob=False)
  away_df = pack.return_away()
  home_df = pack.return_home()
  print(away_df)
  print(home_df)

  #NHL Display
  print("NHL Display")
  date = '2024-11-15'
  nhl = sports.NHL(date)
  df = retrieve.SportsbookReviewAPI(nhl.money_line, 'Money Line', 'Date', date, sport='nhl').return_data()
  print(df)

  #NBA Display
  print("NBA Display")
  date = '2024-11-15'
  nba = sports.NBA(date)
  df = retrieve.SportsbookReviewAPI(nba.money_line, 'Money Line', 'Date', date, sport='nba').return_data()
  print(df)

  #Package Display
  print("NFL Packaged Data")
  week = 9
  nfl = sports.NFL(week)
  df = retrieve.SportsbookReviewAPI(nfl.money_line, 'Money Line', 'Week', week, sport='nfl').return_data()
  pack = package.Package(df)
  df = pack.return_df()
  print(df)

  #Package Multiple NFL Weeks Together
  print("NFL Multi-Week Information")
  df_list = []
  week = 1
  while week <= 10:
    try:
      nfl = sports.NFL(week)
      df = retrieve.SportsbookReviewAPI(nfl.money_line, 'Money Line', 'Week', week, sport='nfl').return_data()
      print("Week ", week)
      pack = package.Package(df)
      df = pack.return_df()
      df_list.append(df)
      week += 1
    except:
      print("Error")
      week += 1

  df = pd.concat(df_list)
  print(df)

  # Retrieve Multiple NHL Days Together
  print("NHL Multi-Day Information")
  df_list = []
  date = '2024-07-01'
  while date != '2024-10-09':
    try:
      nhl = sports.NHL(date)
      df = retrieve.SportsbookReviewAPI(nhl.money_line, 'Money Line', 'Date', date, sport='nhl').return_data()
      print("Date: ", date)
      df_list.append(df)
      date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1))
      date = date.strftime('%Y-%m-%d')
    except:
      print("Error")
      date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1))
      date = date.strftime('%Y-%m-%d')

  df = pd.concat(df_list)
  print(df)
