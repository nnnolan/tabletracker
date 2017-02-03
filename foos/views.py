import math

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from .models import SinglesGame, Player, DoublesGame, Team


@login_required
def index(request):
    recent_singles_games = SinglesGame.objects.order_by('-date')[:10]
    singles_ranking = Player.objects\
        .filter(singles_games_played__gte=4)\
        .order_by('-rating')

    processed_singles_games = []
    for game in recent_singles_games:
        setattr(game, 'player1_rating_change',
                game.player1_end_rating - game.player1_start_rating)
        setattr(game, 'player2_rating_change',
                game.player2_end_rating - game.player2_start_rating)
        processed_singles_games.append(game)

    recent_doubles_games = DoublesGame.objects.order_by('-date')[:10]
    doubles_ranking = Team.objects.order_by('-rating')

    processed_doubles_games = []
    for game in recent_doubles_games:
        setattr(game, 'team1_rating_change',
                game.team1_end_rating - game.team1_start_rating)
        setattr(game, 'team2_rating_change',
                game.team2_end_rating - game.team2_start_rating)
        processed_doubles_games.append(game)

    return render(request, 'foos/index.html', {
        'recent_singles_games' : processed_singles_games,
        'singles_ranking' : singles_ranking,
        'recent_doubles_games' : processed_doubles_games,
        'doubles_ranking' : doubles_ranking,
        'user' : request.user,
    }, content_type='application/xhtml+xml')


@login_required
def new_game(request):
    players = Player.objects.all().order_by('name')
    teams = Team.objects.all()
    # If it isn't a post, we are just going to display the game entry form
    if request.method != 'POST':
        return render(request, 'foos/game.html', {
            'players' : players,
            'teams' : teams,
        })

    else:
        try:
            game_type = request.POST['game_type']
        except KeyError:
            return render(request, 'foos/game.html', {
                'error_message' : 'Invalid POST received! Clown.',
                'players' : players,
                'teams' : teams,
            })

        # Singles game entry
        result = None
        if game_type == "singles":
            result = _validate_and_submit_singles_post(request)
        elif game_type == "doubles":
            result = _validate_and_submit_doubles_post(request)
        else:
            return render(request, 'foos/game.html', {
                'error_message' : 'Invalid game_type received! Clown.',
                'players' : players,
                'teams' : teams,
            })

        if result:
            if result['error']:
                return render(request, 'foos/game.html', {
                    'error_message' : result['error_message'],
                    'players' : players,
                    'teams' : teams,
                })

        # Whew! Okay, the result looks valid.
        return redirect('foos:index')


@login_required
def player(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    # Pull a list of all games played by the player
    singles_games = SinglesGame.objects\
        .filter(Q(player1=player) | Q(player2=player))\
        .order_by('-date')
    processed_singles_games = []
    for game in singles_games:
        setattr(game, 'player1_rating_change',
                game.player1_end_rating - game.player1_start_rating)
        setattr(game, 'player2_rating_change',
                game.player2_end_rating - game.player2_start_rating)
        processed_singles_games.append(game)
    # Build a list of wins/losses vs. every other player
    prob_player_list = _calculate_player_win_probs(player_id)
    # Build probability of winning vs every other player
    return render(request, 'foos/player.html', {
        'player' : player,
        'singles_games' : processed_singles_games,
        'player_probabilities' : prob_player_list
    })


def _calculate_player_win_probs(player_id):
    player = Player.objects.get(id=player_id)
    other_players = Player.objects.exclude(id=player_id)
    results = []
    for other in other_players:
        # Calculate the wins and losses vs. each player
        wins = 0
        losses = 0
        singles1 = SinglesGame.objects.filter(player1=player, player2=other)
        for game in singles1:
            if game.player1_score > game.player2_score:
                wins += 1
            elif game.player2_score > game.player1_score:
                losses += 1
        singles2 = SinglesGame.objects.filter(player1=other, player2=player)
        for game in singles2:
            if game.player1_score > game.player2_score:
                losses += 1
            elif game.player2_score > game.player1_score:
                wins += 1

        # Now calculate the probability of victory based on the rating
        # compared to the other player
        rating_difference = player.rating - other.rating
        base_prob = 1 / (1 + math.pow(10, (rating_difference / 400)))
        probability = 1 - base_prob
        probability = round(probability * 100, 1)
        player_obj = {
            'name' : other.name,
            'probability' : probability,
            'rating' : other.rating,
            'id' : other.id,
            'wins' : wins,
            'losses' : losses,
        }
        results.append( player_obj )

    return results

def _validate_and_submit_singles_post(request):
    return_data = {
        'error' : False,
        'error_message' : '',
        'status_message' : '',
    }

    try:
        player1_id = request.POST['player1']
        player2_id = request.POST['player2']
        player1_score = request.POST['player1_score']
        player2_score = request.POST['player2_score']
    except KeyError:
        return_data['error_message'] = 'Invalid POST received! Clown.'
        return_data['error'] = True
        return return_data

    # Make sure the same player isn't selected
    if player1_id == player2_id:
        return_data['error_message'] = 'You selected the same player! Clown.'
        return_data['error'] = True
        return return_data

    if player1_score == '' or player1_score is None:
        player1_score = 0
    if player2_score == '' or player2_score is None:
        player2_score = 0
    try:
        player1_score = int(player1_score)
        player2_score = int(player2_score)
    except Exception:
        return_data['error_message'] = 'Player score must be an integer! Clown.'
        return_data['error'] = True
        return return_data
    try:
        player1_id = int(player1_id)
        player2_id = int(player2_id)
    except Exception:
        return_data['error_message'] = "Don't try to submit weird data! Clown."
        return_data['error'] = True
        return return_data

    player1 = Player.objects.get(id=player1_id)
    player2 = Player.objects.get(id=player2_id)

    if not player1 and not player2:
        return_data['error_message'] = "Players do not exist! Clown."
        return_data['error'] = True
        return return_data

    # Check the scores to make sure they are in the range of 0-11
    if player1_score < 0 or player1_score > 11:
        return_data['error_message'] = 'Player 1 score was outside the range of 0-11! Clown.'
        return_data['error'] = True
        return return_data
     # Check the scores to make sure they are in the range of 0-11
    if player2_score < 0 or player2_score > 11:
        return_data['error_message'] = 'Player 2 score was outside the range of 0-11! Clown.'
        return_data['error'] = True
        return return_data
    # House rules. If a tiebreaker (win by 2) happened, the winning score must be 11-9.
    if player1_score == 11 or player2_score == 11:
        if player1_score != 9 and player2_score != 9:
            return_data['error_message'] = 'If win-by-two (tiebreaker), the resulting score must be 11-9!'
            return_data['error'] = True
            return return_data
    # House rules, cannot win by 1.
    if player1_score == 10 or player2_score == 10:
        if player1_score == 9 or player2_score == 9:
            return_data['error_message'] = 'If win-by-two (tiebreaker), the resulting score must be 11-9!'
            return_data['error'] = True
            return return_data

    if player1_score != 10 and player2_score != 10 and player1_score != 11 and player2_score != 11:
        if player1_score - player2_score != 0:
            return_data['error_message'] = 'Surely somebody won the game?'
            return_data['error'] = True
            return return_data

    p1_end_rating = _calculate_elo(player1.rating, player2.rating, player1_score, player2_score)
    p2_end_rating = _calculate_elo(player2.rating, player1.rating, player2_score, player1_score)

    s = SinglesGame(
        player1=player1,
        player2=player2,
        player1_score=player1_score,
        player2_score=player2_score,
        player1_start_rating=player1.rating,
        player2_start_rating=player2.rating,
        player1_end_rating=p1_end_rating,
        player2_end_rating=p2_end_rating,
    )
    s.save()

    if player1_score > player2_score:
        player1.singles_wins += 1
        player2.singles_losses += 1
    elif player2_score > player1_score:
        player2.singles_wins += 1
        player1.singles_losses += 1
    else:
        player1.singles_draws += 1
        player2.singles_draws += 1

    # Update ratings
    player1.rating = p1_end_rating
    player2.rating = p2_end_rating
    player1.save()
    player2.save()

    return return_data


def _validate_and_submit_doubles_post(request):
    return_data = {
        'error' : False,
        'error_message' : '',
        'status_message' : '',
    }

    try:
        team1player1 = request.POST['team1player1']
        team1player2 = request.POST['team1player2']
        team2player1 = request.POST['team2player1']
        team2player2 = request.POST['team2player2']
        team1_score = request.POST['team1_score']
        team2_score = request.POST['team2_score']
    except KeyError:
        return_data['error_message'] = 'Invalid POST received! Clown.'
        return_data['error'] = True
        return return_data

    team1 = _validate_and_get_team(team1player1, team1player2)
    if not team1:
        return_data['error_message'] = 'Team 1 is invalid.'
        return_data['error'] = True
        return return_data

    team2 = _validate_and_get_team(team2player1, team2player2)
    if not team2:
        return_data['error_message'] = 'Team 2 is invalid.'
        return_data['error'] = True
        return return_data

    # Make sure the same team isn't selected
    if team1 == team2:
        return_data['error_message'] = 'You selected the same team! Clown.'
        return_data['error'] = True
        return return_data

    if team1_score == '' or team1_score is None:
        team1_score = 0
    if team2_score == '' or team2_score is None:
        team2_score = 0
    try:
        team1_score = int(team1_score)
        team2_score = int(team2_score)
    except Exception:
        return_data['error_message'] = 'team score must be an integer! Clown.'
        return_data['error'] = True
        return return_data

    # Check the scores to make sure they are in the range of 0-11
    if team1_score < 0 or team1_score > 11:
        return_data['error_message'] = 'team 1 score was outside the range of 0-11! Clown.'
        return_data['error'] = True
        return return_data
     # Check the scores to make sure they are in the range of 0-11
    if team2_score < 0 or team2_score > 11:
        return_data['error_message'] = 'team 2 score was outside the range of 0-11! Clown.'
        return_data['error'] = True
        return return_data
    # House rules. If a tiebreaker (win by 2) happened, the winning score must be 11-9.
    if team1_score == 11 or team2_score == 11:
        if team1_score != 9 and team2_score != 9:
            return_data['error_message'] = 'If win-by-two (tiebreaker), the resulting score must be 11-9!'
            return_data['error'] = True
            return return_data
    # House rules, cannot win by 1.
    if team1_score == 10 or team2_score == 10:
        if team1_score == 9 or team2_score == 9:
            return_data['error_message'] = 'If win-by-two (tiebreaker), the resulting score must be 11-9!'
            return_data['error'] = True
            return return_data

    # TODO: Allow draws
    if team1_score != 10 and team2_score != 10 and team1_score != 11 and team2_score != 11:
        if team1_score - team2_score != 0:
            return_data['error_message'] = 'Surely somebody won the game?'
            return_data['error'] = True
            return return_data

    t1_end_rating = _calculate_elo(team1.rating, team2.rating, team1_score, team2_score)
    t2_end_rating = _calculate_elo(team2.rating, team1.rating, team2_score, team1_score)

    s = DoublesGame(
        team1=team1,
        team2=team2,
        team1_score=team1_score,
        team2_score=team2_score,
        team1_start_rating=team1.rating,
        team2_start_rating=team2.rating,
        team1_end_rating=t1_end_rating,
        team2_end_rating=t2_end_rating,
    )
    s.save()

    if team1_score > team2_score:
        team1.wins += 1
        team2.losses += 1
        team1.player1.doubles_wins += 1
        team1.player2.doubles_wins += 1
        team2.player1.doubles_losses += 1
        team2.player2.doubles_losses += 1
    elif team2_score > team1_score:
        team2.wins += 1
        team1.losses += 1
        team2.player1.doubles_wins += 1
        team2.player2.doubles_wins += 1
        team1.player1.doubles_losses += 1
        team1.player2.doubles_losses += 1
    else:
        team1.draws += 1
        team2.draws += 1
        team1.player1.doubles_draws += 1
        team1.player2.doubles_draws += 1
        team2.player1.doubles_draws += 1
        team2.player2.doubles_draws += 1

    team1.player1.save()
    team1.player2.save()
    team2.player1.save()
    team2.player2.save()

    # Update ratings
    team1.rating = t1_end_rating
    team2.rating = t2_end_rating
    team1.save()
    team2.save()

    return return_data


def _validate_and_get_team(player1_id, player2_id):
    try:
        int(player1_id)
        int(player2_id)
    except Exception:
        return None

    player1 = Player.objects.get(id=player1_id)
    player2 = Player.objects.get(id=player2_id)
    if not player1 and not player2:
        return None

    team = Team.objects.filter(player1=player1, player2=player2).first()
    if team:
        return team
    team = Team.objects.filter(player1=player2, player2=player1).first()
    if team:
        return team

    # The team does not exist, so we insert it
    t = Team(player1=player1, player2=player2)
    t.save()

    return t


def _calculate_elo(player_rating, opponent_rating, player_score, opponent_score):
    # sa = actual score
    # ea = expected score

    if player_score < opponent_score:
        sa = 0
    if player_score > opponent_score:
        sa = 1
    if player_score == opponent_score:
        sa = 0.5
    ea = 1 / (1 + math.pow(10, ((opponent_rating - player_rating) / 400)))

    # k = "k-factor"
    k = 32
    if player_rating > 2100 and player_rating < 2400:
        k = 24
    if player_rating > 2400:
        k = 16

    new_rating = player_rating + k * (sa - ea)
    return round(new_rating)
