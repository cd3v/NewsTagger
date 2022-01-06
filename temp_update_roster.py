
from datetime import datetime
from bs4 import BeautifulSoup

import helpers
import shutil
import json
import os
import requests
import unidecode

translations = dict()
#for football ncaa
translations["alabama_bulldogs"] = "alabama_a&m^bulldogs"
translations["florida_rattlers"] = "florida_a&m^rattlers"
translations["miami_oh_redhawks"] = "miami_ohio^redhawks"
translations["north_carolina_aggies"] = "north_carolina_a&t^aggies"
translations["prairie_view_panthers"] = "prairie_view_a&m^panthers"
translations["sam_houston_bearkats"] = "sam_houston_state^bearkats"
translations["san_jos%C3%A9_state_spartans"] = "san_jose_state^spartans"
translations["st_francis_pa_red_flash"] = "st._francis_pennsylvania^red_flash"
translations["st_thomas_minnesota_tommies"] = "st._thomas^tommies"
translations["texas_aggies"] = "texas_a&m^aggies"
translations["william_mary_tribe"] = "william_&_mary^tribe"
#for basketball ncaa
translations["saint_joseph_hawks"] = "saint_josephs^hawks"
translations["st_john_red_storm"] = "st._johns^red_storm"
translations["gardner_webb_runnin_bulldogs"] = "gardner-webb^bulldogs"
translations["saint_peter_peacocks"] = "saint_peters^peacocks"
translations["mount_st_mary_mountaineers"] = "mount_st_marys^mountaineers"
translations["st_francis_bkn_terriers"] = "st._francis_brooklyn^terriers"
translations["loyola_md_greyhounds"] = "loyola_maryland^greyhounds"
translations["texas_cc_islanders"] = "texas_a&m_cc^islanders"
translations["saint_mary_gaels"] = "saint_marys^gaels"
#for soccer mls
translations["chicago^fire_fc"] = "chicago-fire"
translations["houston^dynamo_fc"] = "houston-dynamo"
translations["la^galaxy"] = "los-angeles-galaxy"
translations["los_angeles^fc"] = "los-angeles-fc-lafc"
translations["cf^montreal"] = "montreal-impact"
translations["nashville^sc"] = "nashville-sc-nashville"


def make_historical_copy():
    now = datetime.now()
    now = str(now).replace(' ', '-').replace(':', '-').split('.')[0]
    #shutil.copyfile('betting_dictionaries.py', f'Dictionary_Historical//{now}.py')
    print('Copying to file in folder DATA/master_dictionary_historical')
    shutil.copyfile(os.path.join(rootdir, 'master_dictionary.json'), os.path.join(rootdir, 'master_dictionary_historical', f'{now}.json'))

def clean_names(names):
    names_cleaned = list()
    for name in names:
        if name == None:
            continue
        #UPDATE THIS LINE AS NEEDED
        # name = name.replace(" ", "_")
        # turn T.J. Moore into tj moore and replace accented letters with what they look like without it
        name = name.replace(".", "").replace(" ","_")
        name = unidecode.unidecode(name)
        name = name.lower()
        names_cleaned.append(name)
    return names_cleaned

def get_football_ncaa(teams):
    print("STARTING FOOTBALL NCAA")

    url = "http://www.espn.com/college-football/players"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    teamssite = list()
    for a in soup.find_all("a", href=True):
        u = a['href']
        if "college-football/team/roster" in u:
            t = u.split("/")
            t = t[len(t)-1].replace("-", "_")
            teamssite.append((t, u))

    map = list()
    for ts in teamssite:
        tsname = ts[0]
        if tsname in translations:
            map.append((translations[tsname], ts[1]))
            continue
        found = False
        for team in teams:
            tcompare = team.replace("^", "_").replace("-", "_").replace(".", "")
            if tcompare == tsname:
                map.append((team, ts[1]))
                found = True
                break
        if not found:
            print(f"---> ERROR: football ncaa had issue mapping {tsname} to master_dictionary")
            continue
    for team, url in map:
        print(team, url)
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        names = list()
        for a in soup.find_all("a", href=True):
            u = a['href']
            if "college-football/player" in u:
                names.append(a.string)

        names_cleaned = clean_names(names)
        if len(names_cleaned) == 0:
            print(f"---> ERROR: football ncaa {team} had issue accessing the webpage {url}")
            continue
        names_sorted = sorted(names_cleaned)
        roster = dict()
        for name in names_sorted:
            roster[name] = dict()
        teams[team]["roster"] = roster
    return teams

def get_football_nfl(teams):
    print("STARTING FOOTBALL NFL")

    for team in teams:
        t = team.replace("_", "-").replace("^", "-")
        url = f'https://www.nfl.com/teams/{t}/roster'
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        names = [n.text.strip() for n in soup.find_all(class_="nfl-o-roster__player-name nfl-o-cta--link")]

        names_cleaned = clean_names(names)
        if len(names_cleaned) == 0:
            print(f"---> ERROR: football nfl {t} had issue accessing the webpage {url}")
            continue
        names_sorted = sorted(names_cleaned)
        roster = dict()
        for name in names_sorted:
            roster[name] = dict()
        teams[team]["roster"] = roster
    return teams

""" unable to find a site """
def get_baseball_ncaa(teams):
    print("STARTING BASEBALL NCAA -- Unable to find rosters")
    return teams

def get_baseball_mlb(teams):
    print("STARTING BASEBALL MLB")
    for team in teams:
        url = f'https://www.lineups.com/mlb/roster/{team.replace("^", "-").replace("_", "-")}'
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        names = [n.text.strip() for n in soup.find_all(class_="player-name-col-lg")]

        names_cleaned = clean_names(names)
        if len(names_cleaned) == 0:
            print(f"---> ERROR: baseball mlb {team} had issue accessing the webpage {url}")
            continue
        names_sorted = sorted(names_cleaned)
        roster = dict()
        for name in names_sorted:
            roster[name] = dict()
        teams[team]["roster"] = roster
    return teams


def get_basketball_ncaa(teams):
    print("STARTING BASKETBALL NCAA")

    url = "http://www.espn.com/mens-college-basketball/players"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    teamssite = list()
    for a in soup.find_all("a", href=True):
        u = a['href']
        if "mens-college-basketball/team/roster" in u:
            t = u.split("/")
            t = t[len(t)-1].replace("-", "_")
            teamssite.append((t, u))

    map = list()
    for ts in teamssite:
        tsname = ts[0]
        if tsname in translations:
            map.append((translations[tsname], ts[1]))
            continue
        found = False
        for team in teams:
            tcompare = team.replace("^", "_").replace("-", "_").replace(".", "")
            if tcompare == tsname:
                map.append((team, ts[1]))
                found = True
                break
        if not found:
            print(f"---> ERROR: basketball ncaa had issue mapping {tsname} to master_dictionary")
            continue
    for team, url in map:
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        names = list()
        for a in soup.find_all("a", href=True):
            u = a['href']
            if "mens-college-basketball/player" in u:
                names.append(a.string)

        names_cleaned = clean_names(names)
        if len(names_cleaned) == 0:
            print(f"---> ERROR: basketball ncaa {team} had issue accessing the webpage {url}")
            continue
        names_sorted = sorted(names_cleaned)
        roster = dict()
        for name in names_sorted:
            roster[name] = dict()
        teams[team]["roster"] = roster
    return teams

def get_basketball_nba(teams):
    print("STARTING BASKETBALL NBA")

    for team in teams:
        url = f'https://www.lineups.com/nba/roster/{team.replace("^", "-").replace("_", "-")}'
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        names = [n.text.strip() for n in soup.find_all(class_="player-name-col-lg")]

        names_cleaned = clean_names(names)
        if len(names_cleaned) == 0:
            print(f"---> ERROR: basketball nba {team} had issue accessing the webpage {url}")
            continue
        names_sorted = sorted(names_cleaned)
        roster = dict()
        for name in names_sorted:
            roster[name] = dict()
        teams[team]["roster"] = roster
    return teams


def get_hockey_nhl(teams):
    print("STARTING HOCKEY NHL")

    for team in teams:
        #toronto|maple-leafs -> mapleleafs which is what the website url uses
        t = team.split("^")[1].replace("_", "")
        url = f'https://www.nhl.com/{t}/roster'
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        firstnames = [n.text.strip() for n in soup.find_all(class_="name-col__item name-col__firstName")]
        lastnames = [n.text.strip() for n in soup.find_all(class_="name-col__item name-col__lastName")]
        names = list()
        for i in range(len(firstnames)):
            names.append(firstnames[i]+" "+lastnames[i])

        names_cleaned = clean_names(names)
        if len(names_cleaned) == 0:
            print(f"---> ERROR: hockey nhl {t} had issue accessing the webpage {url}")
            continue
        names_sorted = sorted(names_cleaned)
        roster = dict()
        for name in names_sorted:
            roster[name] = dict()
        teams[team]["roster"] = roster
    return teams

def get_soccer_mls(teams):
    print("STARTING SOCCER MLS")

    for team in teams:
        t = ""
        if team in translations:
            t = translations[team]
        else:
            t = team.replace("^", "-").replace("_", "-")
        url = f'https://www.foxsports.com/soccer/{t}-team-roster'
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        names = [n.text.strip() for n in soup.find_all(class_="table-entity-name ff-s")]


        names_cleaned = clean_names(names)
        if len(names_cleaned) == 0:
            print(f"---> ERROR: soccer mls {team} had issue accessing the webpage {url}")
            continue
        names_sorted = sorted(names_cleaned)
        roster = dict()
        for name in names_sorted:
            roster[name] = dict()
        teams[team]["roster"] = roster
    return teams

def get_soccer_epl(teams):
    print("STARTING SOCCER MLS")

    #found no site that was easy to get the roster from the team name
    translations["arsenal"] = "https://www.espn.com/soccer/team/squad/_/id/359/arsenal"
    translations["aston_villa"] = "https://www.espn.com/soccer/team/squad/_/id/362/aston-villa"
    translations["brentford"] = "https://www.espn.com/soccer/team/squad/_/id/337/brentford"
    translations["brighton_&_hove_albion^fc"] = "https://www.espn.com/soccer/team/squad/_/id/331/brighton-&-hove-albion"
    translations["burnley"] = "https://www.espn.com/soccer/team/squad/_/id/379/burnley"
    translations["chelsea"] = "https://www.espn.com/soccer/team/squad/_/id/363/chelsea"
    translations["crystal_palace"] = "https://www.espn.com/soccer/team/squad/_/id/384/crystal-palace"
    translations["everton"] = "https://www.espn.com/soccer/team/squad/_/id/368/everton"
    translations["leeds_united"] = "https://www.espn.com/soccer/team/squad/_/id/357/leeds-united"
    translations["leicester_city"] = "https://www.espn.com/soccer/team/squad/_/id/375/leicester-city"
    translations["liverpool"] = "https://www.espn.com/soccer/team/squad/_/id/364/liverpool"
    translations["manchester_city"] = "https://www.espn.com/soccer/team/squad/_/id/382/manchester-city"
    translations["manchester_united"] = "https://www.espn.com/soccer/team/squad/_/id/360/manchester-united"
    translations["newcastle_united"] = "https://www.espn.com/soccer/team/squad/_/id/361/newcastle-united"
    translations["norwich_city"] = "https://www.espn.com/soccer/team/squad/_/id/381/norwich-city"
    translations["southampton"] = "https://www.espn.com/soccer/team/squad/_/id/376/southampton"
    translations["tottenham_hotspur"] = "https://www.espn.com/soccer/team/squad/_/id/367/tottenham-hotspur"
    translations["watford"] = "https://www.espn.com/soccer/team/squad/_/id/395/watford"
    translations["west_ham_united"] = "https://www.espn.com/soccer/team/squad/_/id/371/west-ham-united"
    translations["wolverhampton_wanderers"] = "https://www.espn.com/soccer/team/squad/_/id/380/wolverhampton-wanderers"

    for team in teams:
        url = translations[team]
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        names = list()
        for a in soup.find_all("a", href=True):
            u = a['href']
            if "player/_/id" in u:
                names.append(a.string)

        names_cleaned = clean_names(names)
        if len(names_cleaned) == 0:
            print(f"---> ERROR: basketball ncaa {team} had issue accessing the webpage {url}")
            continue
        names_sorted = sorted(names_cleaned)
        roster = dict()
        for name in names_sorted:
            roster[name] = dict()
        teams[team]["roster"] = roster
    return teams

def get_tennis_men(teams):
    print("STARTING TENNIS MEN")

    url = "https://www.espn.com/tennis/rankings"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    names = list()
    for a in soup.find_all("a", href=True):
        u = a['href']
        if "tennis/player/_/id" in u:
            #a.string gets what the hyperlink is displayed as on the page (the acutal name)
            names.append(a.string)

    names_cleaned = clean_names(names)
    if len(names_cleaned) == 0:
        print(f"---> ERROR: tennis men had issue accessing the webpage {url}")
        return teams
    names_sorted = sorted(names_cleaned)
    roster = dict()
    for name in names_sorted:
        roster[name] = dict()
    teams["roster"] = roster

    return teams

def get_fighting_boxing(teams):
    print("STARTING FIGHTING BOXING")

    url = "https://boxingrankings.co/"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    names = [n.text.strip() for n in soup.find_all(class_="s3")]

    names_cleaned = clean_names(names)
    if len(names_cleaned) == 0:
        print(f"---> ERROR: fighting boxing had issue accessing the webpage {url}")
        return teams
    names_sorted = sorted(names_cleaned)
    roster = dict()
    for name in names_sorted:
        roster[name] = dict()
    teams["roster"] = roster
    print(roster)
    quit()
    return teams

def get_golf_men(teams):
    print("STARTING GOLF MEN")

    url = "https://www.cbssports.com/golf/rankings/"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    names = list()

    for n in soup.find_all(class_="CellPlayerName--long"):
        for a in n.find_all("a", href=True):
            names.append(a.string)

    names_cleaned = clean_names(names)
    if len(names_cleaned) == 0:
        print(f"---> ERROR: golf men had issue accessing the webpage {url}")
        return teams
    names_sorted = sorted(names_cleaned)
    roster = dict()
    for name in names_sorted:
        roster[name] = dict()
    teams["roster"] = roster

    return teams

def writefile(data):
    print("not acutally writing file")
    quit()
    with open(os.path.join(rootdir, "master_dictionary.json"), "w") as outfile:
        json.dump(data, outfile, sort_keys=False, indent=2)

if __name__ == "__main__":
    rootdir = "DATA"
    master = helpers.open_file(os.path.join(rootdir, 'master_dictionary'))

    # make_historical_copy()

    #master["teams"]["baseball"]["ncaa"] = get_baseball_ncaa(master["teams"]["baseball"]["ncaa"])
    #writefile(master)

    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["baseball"]["mlb"] = get_baseball_mlb(master["teams"]["baseball"]["mlb"])
    # writefile(master)

    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["basketball"]["nba"] = get_basketball_nba(master["teams"]["basketball"]["nba"])
    # writefile(master)

    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["basketball"]["ncaa"] = get_basketball_ncaa(master["teams"]["basketball"]["ncaa"])
    # writefile(master)

    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["football"]["nfl"] = get_football_nfl(master["teams"]["football"]["nfl"])
    # writefile(master)

    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["football"]["ncaa"] = get_football_ncaa(master["teams"]["football"]["ncaa"])
    # writefile(master)
    #
    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["hockey"]["nhl"] = get_hockey_nhl(master["teams"]["hockey"]["nhl"])
    # writefile(master)

    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["soccer"]["mls"] = get_soccer_mls(master["teams"]["soccer"]["mls"])
    # writefile(master)

    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["soccer"]["epl"] = get_soccer_epl(master["teams"]["soccer"]["epl"])
    # writefile(master)

    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["tennis"]["men"]["tennis|men"] = get_tennis_men(master["teams"]["tennis"]["men"]["tennis|men"])
    # writefile(master)
    #
    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["fighting"]["boxing"]["fighting|boxing"] = get_fighting_boxing(master["teams"]["fighting"]["boxing"]["fighting|boxing"])
    # writefile(master)
    #
    # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
    # master["teams"]["golf"]["men"]["golf|men"] = get_golf_men(master["teams"]["golf"]["men"]["golf|men"])
    # writefile(master)
