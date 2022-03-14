from pydoc import cli
from unicodedata import name
import click
import requests
import csv
import json
import sqlite3

BASE_URL = "https://www.balldontlie.io/api/v1/"
LBS_KG_RATIO = 2.205
INCH_CM_RATIO = 2.54
FOOT_INCH_RATIO = 12


def fetch_data(endpoint):
    '''Sends a request to the server and fetches data in json format'''
    r = requests.get(BASE_URL + endpoint)
    json_data = r.json()
    return json_data

def get_divisions(data):
    '''Creates a list of team divisions'''
    divisions = []
    for team in data["data"]:
        if team['division'] not in divisions:
           divisions.append(team['division'])
    return divisions

def unit_conversion(measurement, unit):
    '''Converts units to international system'''
    try:
        if unit == 'lbs':
            return round(measurement / LBS_KG_RATIO)
        elif unit == 'inches':
            feet_to_inch = measurement[0] * FOOT_INCH_RATIO
            return round((feet_to_inch + measurement[1]) * \
                          INCH_CM_RATIO / 100, 2)
    except:
        print('Couldn\'t convert the units')

@click.group()
def cli():
    '''Creates a click module command group '''
    pass

@click.command('grouped-teams')
def fetch_teams():
    '''Fetches all teams and groups them by division '''
    data = fetch_data('teams')
    divisions = get_divisions(data)
    for division in divisions:
        print(division)
        for team in data["data"]:
            if team['division'] == division:
                team_name, abb = team['full_name'], team['abbreviation']
                print(f'\t{team_name} ({abb})')

def get_tallest_p(json_pages):
    '''Gets the tallest player and their information '''
    tallest_p = {}
    for dictionary in json_pages:
        if dictionary["height_feet"] == None:
            pass
        elif len(tallest_p) == 0:
            tallest_p["name"] = dictionary["first_name"] + \
                                " " + dictionary["last_name"]
            tallest_p["height"] = [dictionary["height_feet"], 
                                   dictionary["height_inches"]]
        elif tallest_p["height"][0] < dictionary["height_feet"]:
            tallest_p["name"] = dictionary["first_name"] + \
                                " " + dictionary["last_name"]
            tallest_p["height"][0], tallest_p["height"][1] = dictionary["height_feet"], \
                                                            dictionary["height_inches"]
        elif tallest_p["height"][0] == dictionary["height_feet"]:
            if tallest_p["height"][1] < dictionary["height_inches"]:
                tallest_p["name"] = dictionary["first_name"] + \
                                    " " + dictionary["last_name"]
                tallest_p["height"][1] = dictionary["height_inches"]
    return tallest_p

def get_heaviest_p(json_pages):
    '''Gets the heaviest player and their information'''
    heaviest_p = {}
    for dictionary in json_pages:
        if dictionary["weight_pounds"] == None:
            pass
        elif len(heaviest_p) == 0:
            heaviest_p["name"] = dictionary["first_name"] + \
                                 " " + dictionary["last_name"]
            heaviest_p["weight_pounds"] = dictionary["weight_pounds"]
        elif heaviest_p["weight_pounds"] < dictionary["weight_pounds"]:
            heaviest_p["name"] = dictionary["first_name"] + \
                                 " " + dictionary["last_name"]
            heaviest_p["weight_pounds"] = dictionary["weight_pounds"]
    return heaviest_p

@click.command('player-stats')
@click.option("--name", default=None, type=str, 
              required=True, help="Gets a player with a specific name")
def fetch_player_stats(name):
    '''Prints out the heaviest and talles players to the console'''
    tallest_p, heaviest_p = {}, {}
    try:
        json_pages = []
        buffor = fetch_data('players' + f'/?search={name}')
        while True:
            json_pages.extend(buffor["data"])
            if buffor["meta"]["next_page"] == None:
                break
            buffor = fetch_data('players' + 
                     f'/?search={name}&page={buffor["meta"]["next_page"]}')
        tallest_p, heaviest_p = get_tallest_p(json_pages), \
                                get_heaviest_p(json_pages)
    except:
        print('Failed to get the player statistics.')
    finally:
        if len(tallest_p) == 0:
            print("The tallest player: Not found")
        else:
            print("The tallest player: ", tallest_p["name"], 
                  unit_conversion(tallest_p["height"], 'inches'), 'meters')
        if len(heaviest_p) == 0:
            print("The heaviest player: Not found")
        else:
            print("The heaviest player: ", heaviest_p["name"], 
                  unit_conversion(heaviest_p["weight_pounds"], 'lbs'), 'kilograms')

@click.command('teams-stats')
@click.option("--season", default=None, type=str, 
              required=True, help="Provides statistic for a particulars season")
@click.option("--output", default='stdout', type=str, 
              required=False, help="Transforms the output into the selected form")
def fetch_teams_stats(season, output):
    '''Gets all the team stats for a particular season and directs it to a chosen output'''
    json_pages = []
    teams_stats = {}
    buffor = fetch_data('games' + f'/?seasons[]={season}')
    print(f'Loading data for {season} season...')
    while True:
        json_pages.extend(buffor["data"])
        if buffor["meta"]["next_page"] == None or buffor["meta"]["next_page"] == "null":
            break

        buffor = fetch_data('games' + 
                f'/?seasons[]={season}&page={buffor["meta"]["next_page"]}')

    for dictionary in json_pages:
        home_team = dictionary["home_team"]["full_name"] + \
                    f' ({dictionary["home_team"]["abbreviation"]})'

        visitor_team = dictionary["visitor_team"]["full_name"] + \
                       f' ({dictionary["visitor_team"]["abbreviation"]})'
        if home_team not in teams_stats.keys():
            teams_stats[home_team] = [0, 0, 0, 0]

        if visitor_team not in teams_stats.keys():
            teams_stats[visitor_team] = [0, 0, 0, 0]

        if dictionary["home_team_score"] == dictionary["visitor_team_score"]:
            pass
        else:
            home_team_won = dictionary["home_team_score"] > dictionary["visitor_team_score"]
            if home_team_won:
                teams_stats[home_team][0] += 1
                teams_stats[visitor_team][3] += 1
            else:
                teams_stats[home_team][2] += 1
                teams_stats[visitor_team][1] += 1

    if output == 'stdout':
        for key, value in teams_stats.items():
            print(key, '\n', ' ', f'won games as home team: {value[0]}', '\n',
                            ' ', f'won games as visitor team: {value[1]}', '\n',
                            ' ', f'lost games as home team: {value[2]}', '\n',
                            ' ', f'lost games as visitor team: {value[3]}', '\n',)

    elif output == 'csv':
        f = open("teams-stats.csv", 'w', newline="")
        writer = csv.writer(f)
        writer.writerow(('Team name', 
                        'Won games as home team', 
                        'Won games as visitor team', 
                        'Lost games as home team',
                        'Lost games as visitor team'))
        for key, value in teams_stats.items():
            t = (key, value[0], value[1], value[2], value[3])
            writer.writerow(t)
        f.close()

    elif output == 'json':
        f = open("teams-stats.json", 'w')
        for key, value in teams_stats.items():
            data = {}
            data['team_name'] = key
            data['Won games as home team'] = value[0]
            data['Won games as visitor team'] = value[1]
            data['Lost games as home team'] = value[2]
            data['Lost games as visitor team'] = value[3]
            json.dump(data, f)
            f.write(',')
        f.close()
    
    # Not finished - sqlite output
    # elif output == 'sqlite':
    #     con = sqlite3.connect('team-stats.sql')
    #     cur = con.cursor()
    #     cur.execute('''CREATE TABLE team_stats
    #                         (team_name text PRIMARY KEY, 'Won games as home team' text,    
    #                          'Won games as visitor team text' text)''')
    #     con.commit()

def main():
    cli.add_command(fetch_player_stats)
    cli.add_command(fetch_teams)
    cli.add_command(fetch_teams_stats)
    cli()

if __name__ == "__main__":
    main()
    

