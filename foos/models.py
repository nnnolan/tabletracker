import datetime

from dateutil import tz
from django.db import models


class Player(models.Model):
    name = models.CharField(max_length=100)
    singles_wins = models.IntegerField(default=0)
    singles_losses = models.IntegerField(default=0)
    singles_draws = models.IntegerField(default=0)
    singles_games_played = models.IntegerField(default=0)
    doubles_wins = models.IntegerField(default=0)
    doubles_losses = models.IntegerField(default=0)
    doubles_draws = models.IntegerField(default=0)
    doubles_games_played = models.IntegerField(default=0)
    rating = models.IntegerField(default=1000)

    def __str__(self):
        return "%s" % (self.name)


class SinglesGame(models.Model):
    player1 = models.ForeignKey(Player, related_name='singles_team1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(Player, related_name='singles_team2', on_delete=models.CASCADE)
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    player1_start_rating = models.IntegerField(default=1000)
    player2_start_rating = models.IntegerField(default=1000)
    player1_end_rating = models.IntegerField(default=1000)
    player2_end_rating = models.IntegerField(default=1000)
    date = models.DateTimeField(default=datetime.datetime.now,
                                blank=True)

    def get_winner(self):
        if self.player1_score > self.player2_score:
            return self.player1
        else:
            return self.player2

    @property
    def get_date_string(self):
        desired_tz = tz.gettz('EST')
        modified_time = self.date.astimezone(desired_tz)
        return modified_time.strftime('%m/%d %I:%M %p')

    def __str__(self):
        return "%s vs. %s" % (self.player1,
                              self.player2)


class Team(models.Model):
    player1 = models.ForeignKey(Player, related_name='team_player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(Player, related_name='team_player2', on_delete=models.CASCADE)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    rating = models.IntegerField(default=1000)

    def __str__(self):
        return "%s, %s" % (self.player1.name,
                           self.player2.name)


class DoublesGame(models.Model):
    team1 = models.ForeignKey(Team, related_name='doubles_team1', on_delete=models.CASCADE)
    team2 = models.ForeignKey(Team, related_name='doubles_team2', on_delete=models.CASCADE)
    team1_score = models.IntegerField(default=0)
    team2_score = models.IntegerField(default=0)
    team1_start_rating = models.IntegerField(default=1000)
    team2_start_rating = models.IntegerField(default=1000)
    team1_end_rating = models.IntegerField(default=1000)
    team2_end_rating = models.IntegerField(default=1000)
    date = models.DateTimeField(default=datetime.datetime.now,
                                blank=True)

    @property
    def get_date_string(self):
        desired_tz = tz.gettz('EST')
        modified_time = self.date.astimezone(desired_tz)
        return modified_time.strftime('%m/%d %I:%M %p')

    def _str__(self):
        return "%s vs. %s" % (self.team1, self.team2)
