import pandas as pd

class NaiveBayes():
  """
  A simple implementation of a Naive Bayes Model.
  """
  def __init__(self, set_home_away: str, data: pd.DataFrame):
    """
    Initialize the Naive Bayes model for the data [data] and whether the lines
    are for a home or away team [set_home_away].
    """
    self.home_away = set_home_away
    self.data = data

  def number_wins(self):
    """
    Counts the number of wins in the data.
    """
    return sum(self.data[f"{self.home_away} W/L"])
  
  def number_losses(self):
    """
    Counts the number of losses in the data.
    """
    return len(self.data[f"{self.home_away} W/L"]) - sum(self.data[f"{self.home_away} W/L"])
  
  def win_data(self):
    """
    Returns data containing only the win rows.
    """
    return self.data[self.data[f"{self.home_away} W/L"] == 1]
  
  def loss_data(self):
    """
    Returns the data containing only the loss rows.
    """
    return self.data[self.data[f"{self.home_away} W/L"] == 0]

  def probability(self, x: list) -> float:
    """
    Calculate the probability of a win given a set of features (x) is a list of 
    7 features which matches with the proper organization of sportsbooks found 
    within the data.
    """
    #Calculate the number of wins and losses
    wins = self.number_wins()
    losses = self.number_losses()

    #Set the data preservation lists
    win_num = []
    loss_num = []

    #Find probabilities of each line in x
    for i in range(len(x)):
      #Set the line for sportsbook i
      line = x[i]

      #Calculate P(Line|Win) = # line when win / # wins
      num_line_win = 0
      win_df = self.win_data().reset_index(drop=True)
      for n in range(len(win_df)):
        if len(win_df[f"{self.home_away} Lines"][n]) < len(x):
          continue
        if win_df[f"{self.home_away} Lines"][n][i] == line:
          num_line_win += 1

      #Calculate P(Line|Loss) = # line when loss / # losses
      num_line_loss = 0
      loss_df = self.loss_data().reset_index(drop=True)
      for n in range(len(loss_df)):
        #If the game does not include enough data, do not include it
        if len(loss_df[f"{self.home_away} Lines"][n]) < len(x):
          continue
        if loss_df[f"{self.home_away} Lines"][n][i] == line:
          num_line_loss += 1

      #To avoid rounding errors, preserve data in list and calculate at the end.
      win_num.append(num_line_win)
      loss_num.append(num_line_loss)

    #Calculate probability using Naive Bayes: P(Win|X) ∝ P(Win) * Π P(line_i|Win)
    #Prior is applied once, not once per feature.
    num = wins / len(self.data)
    for i in win_num:
      num *= i / wins

    denom_loss = losses / len(self.data)
    for i in loss_num:
      denom_loss *= i / losses

    denom = num + denom_loss

    #If there is a division by zero, the probability does not have enough information.
    try:
      return num / denom
    except:
      return None





      

    