from .helpers import *
import os
import copy
import nltk
import re
import glob
from os.path import exists

#load in the dictionary that contains the rosters

#for layer_lookup
master = dict()
stopwords = dict()

#for layer_tfidf
terms = dict()

#hold the certain matching words
cmw = dict()

nouns = ['unigram', 'bigram', 'trigram']
H_TOK = "<H><H>"
A_TOK = "<A><A>"
PRINTDEBUG = False
# PRINTDEBUG = True
PRINTDEBUGDEEPER = False
# PRINTDEBUGDEEPER = True



#determines direction of slash for windows or linux system
slash = ('\\' if os.name == 'nt' else '/')

def load_in_terms(rootdata, tfidf_root, master_filename, stopwords_filename, certain_match_words):
    global terms
    global stopwords
    global master
    global cmw
    print("Loading in dictionaries from directory DATA/")
    master = open_file(rootdata + master_filename)
    cmw = open_file(rootdata + certain_match_words)
    stopwords = open_file(rootdata + stopwords_filename)

    for subdir, dirs, files in os.walk(rootdata + tfidf_root):
        #the if is to prevent the code from entering the historical logs to search
        #for matches, since we only care about the current... currently
        historical = 'historical'
        if subdir == rootdata + tfidf_root + 'FAILED':
            continue
        if subdir[-len(historical):] == historical:
            continue
        for file in files:
            terms[os.path.join(subdir, file)] = open_file(os.path.join(subdir, file))
    #stopwords = open_file("stopwords.json")
    print("Finished Loading in dictionaries")

load_in_terms(
    f"./DATA{slash}",
    f"./DATA/TFIDF_DATA{slash}",
    "master_dictionary.json",
    "stopwords",
    "certain_match_words"
)


#points per gram match, scores are modeled off of fibonacci
# ppg = [3,5,8,13,21]
ppg = [1,3,7,15,31]

#only 1 instance of this exists that all Field classes have access to in order to track what the optimal
#amount of points scored is
class MaxPoints:
    def __init__(self):
        self.sport_matches = list()
        self.sport_points  = 0

        self.league_matches = list()
        self.league_points = 0

        self.team_matches = list()
        self.team_points   = 0

        self.player_matches = list()
        self.player_points = 0


#used only for layer tfidf
class ProbNP:
    def __init__(self, noun_phrase):
        self.id = noun_phrase
        #count not used currently but should so that scoring takes into account if a np repeats (saying touchdown a lot is important)
        self.count = 1 #counts the number of times the np has been seen
        self.sum = 0

    def increment_sum(self, val):
        self.sum += val

    def seen_again(self):
        self.count += 1

class Field:
    def __init__(self, n, m):
        #see explanation.txt number 1 for self.matched_with
        self.name = n
        self.max = m
        self.points = 0
        self.certain_match = False
        self.matched_with = list()
        self.c = dict() #children, like sport will have leagues as a child
        self.bpnp = dict()
        #BEST PER NOUN PHRASE;this is very important
        #if nfl for a given np has 3 hits each of 5 points, it will only
        #get the highest score (5) instead of 15, this is to prevent leagues
        #with a lot of teams from being over done


"""
These exist for flexibility if I want to provide specific scoring/behaviors to each type
"""
class Sport(Field):
    pass
class League(Field):
    pass
class Team(Field):
    def __init__(self, n, m):
        super().__init__(n, m)
        self.certain_match_name = None
class Player(Field):
    def __init__(self, n, m):
        super().__init__(n, m)
        #see explanation.txt number 1 for self.matched_with
        self.fn = None
        self.ln = None
        self.certain_match_name = None
        self.get_first_and_last_names(n.replace("_", " "))

    def get_first_and_last_names(self, name):
        parts = name.split()
        if len(parts) == 1:
            self.fn = name
        else:
            self.fn = parts[0]
            self.ln = " ".join(parts[1:])
class TopMatch:
    def __init__(self, id):
        #identifier is unique to each noun phrase
        #given the noun phrase breakdown for "Kent State Golden Flashes",
        #ID ->Kent State Golden Flashes, Kent State State Golden Golden Flashes, Kent State Golden State Golden Flashes, Kent State Golden Flashes
        self.identifier = id
        self.np_len = len(id.split(",")[-1:][0].split())
        self.best_match_len = 0
        self.exact_match = False
        self.matches = list()

    def get_matches(self):
        return self.matches


    """
    given a Match class object, if it is better than any of the previous matches
    then delete the worser ones. Or if it is of equal value, append it to the list
    """
    def update_best(self, match):
        midlen = len(match.get_mw().split())
        sidlen = self.np_len
        exact = midlen == len(match.id.split())
        #only allow exact_match to fit for bigrams and longer
        #potentially only allow it to work on teams only as well
        if len(self.matches) == 0:
            self.matches.append(match)
            self.best_match_len = midlen
            if sidlen != 1 and exact:
                self.exact_match = True
        elif self.exact_match == True:
            if exact:
                self.matches.append(match)
        else:
            if sidlen != 1 and exact:
                self.matches = [match]
                self.exact_match = True
            else:
                if self.best_match_len > midlen:
                    return
                elif self.best_match_len == midlen:
                    self.matches.append(match)
                else:
                    self.matches = [match]
                    self.best_match_len = midlen

class Match:
    def __init__(self, np_identifier, identifier, mw, s=None, l=None, t=None, c=None, m=None, p=None):
        self.np_identifier = np_identifier
        self.id = identifier
        self.matched_with = mw
        self.sport = s
        self.league = l
        self.team = t #Philadelphia Eagles
        self.city = c #Philadelphia
        self.mascott = m #Eagles
        self.player = p

    def update_match(self, mw):
        self.matched_with = mw

    def get_mw(self):
        return self.matched_with

    def get_noun_identifier(self):
        return self.np_identifier

    def get_id(self):
        return self.id

    def __repr__(self):
        return f"Class_Match:{self.id}"


"""
class noun_phrase:
	def __init__ (self, nphrase):
        self.np = nphrase
        self.matches = list()
"""
def add_points(points, prob):
    if prob == True or points == True:
        return True
    else:
        return points+prob

def print_sltp_matched_with(scores):
    for s in scores:
        print(f"{s}: {scores[s].points} {scores[s].certain_match}")
        for l in scores[s].c:
            print(f"    {l}: {scores[s].c[l].points} {scores[s].c[l].certain_match}")
            for t in scores[s].c[l].c:
                print(f"        {t}: {scores[s].c[l].c[t].points} {scores[s].c[l].c[t].matched_with} {scores[s].c[l].c[t].certain_match}")
                for p in scores[s].c[l].c[t].c:
                    print(f"            {p}: {scores[s].c[l].c[t].c[p].points} {scores[s].c[l].c[t].c[p].matched_with} {scores[s].c[l].c[t].c[p].certain_match}")

#creates a list of unique NP's that a team/player matched with and updates certain match if True
def helper_to_generate_scores(d, n, mw):
    if mw not in d.matched_with:
        if n.replace("^", " ").replace("_", " ") == mw:
            d.certain_match = True
            d.certain_match_name = mw
        d.matched_with.append(mw)

    return d

def helper_to_calculate_points(l):
    points = 0
    for element in l:
        points += ppg[len(element.split())-1]
    return points

#returns a dict type with any sports/leagues that are certain matches because a NP matched the file certain_match_words.json
def get_certain_match_words(all_np, max):
    scores = dict()
    for np_whole in all_np:
        for np_parts in np_whole:
            for np_part in np_parts:
                np_article = np_part.lower().replace(".", "")
                if np_article in cmw:
                    s = cmw[np_article][0] #0th spot holds the sport
                    l = (cmw[np_article][1] if len(cmw[np_article]) > 1 else None) #the 1st spot may or may not hold a league
                    if s not in scores:
                        scores[s] = Sport(s, max)
                        scores[s].certain_match = True
                    if l != None and l not in scores[s].c:
                        scores[s].c[l] = League(l, max)
                        scores[s].c[l].certain_match = True
    return scores

def generate_scores(best_matches, max, scores):
    certain_matches = dict()
    for npid in best_matches:
        #get the points for each of the matches for each NP and find the max for a given sport/league/team/player
        for match in best_matches[npid].get_matches():
            s = match.sport
            l = match.league
            t = match.team
            p = match.player
            if s not in scores:
                scores[s] = Sport(s, max)
            if l not in scores[s].c:
                scores[s].c[l] = League(l, max)
            if t not in scores[s].c[l].c:
                scores[s].c[l].c[t] = Team(t, max)
            if p != None and p not in scores[s].c[l].c[t].c:
                scores[s].c[l].c[t].c[p] = Player(p, max)

            if p == None:
                scores[s].c[l].c[t] = helper_to_generate_scores(scores[s].c[l].c[t], t, match.get_mw())
                #multiple certain matches for the same team name
                if scores[s].c[l].c[t].certain_match:
                    if len(best_matches[npid].get_matches()) > 1:
                        if npid not in certain_matches:
                            certain_matches[npid] = list()
                        certain_matches[npid].append((s,l,t,p))
                        scores[s].c[l].c[t].certain_match = False
                    else:
                        scores[s].c[l].certain_match = True
                        scores[s].certain_match = True
            else:
                scores[s].c[l].c[t].c[p] = helper_to_generate_scores(scores[s].c[l].c[t].c[p], p, match.get_mw())
                #multiple certain matches for the same player name
                if scores[s].c[l].c[t].c[p].certain_match:
                    if len(best_matches[npid].get_matches()) > 1:
                        if npid not in certain_matches:
                            certain_matches[npid] = list()
                        certain_matches[npid].append((s,l,t,p))
                        scores[s].c[l].c[t].c[p].certain_match = False
                    else:
                        scores[s].c[l].c[t].certain_match = True
                        scores[s].c[l].certain_match = True
                        scores[s].certain_match = True

    for s in scores:
        sport_matches_inner = list()
        # print(s)
        for l in scores[s].c:
            league_matches_inner = list()
            # print(f"    {l}")
            for t in scores[s].c[l].c:
                team_matches_inner = scores[s].c[l].c[t].matched_with
                # print(f"        {t}")
                #the team didn't match, so that must mean a player name matched
                for p in scores[s].c[l].c[t].c:
                    player_matches_inner = list()
                    for player_match in scores[s].c[l].c[t].c[p].matched_with:
                        # print(f"            {player_match}")
                        #only a player name fully or partially matched, not the team
                        if len(scores[s].c[l].c[t].matched_with) == 0:
                            if scores[s].c[l].c[t].c[p].certain_match and player_match not in team_matches_inner:
                                if player_match not in max.player_matches:
                                    max.player_matches.append(player_match)
                                player_matches_inner.append(player_match)
                        else:
                            if (scores[s].c[l].c[t].c[p].certain_match or re.search(r"\b" + re.escape(player_match) + r"\b", scores[s].c[l].c[t].c[p].ln)) and player_match not in team_matches_inner:
                                if player_match not in max.player_matches:
                                    max.player_matches.append(player_match)
                                player_matches_inner.append(player_match)
                    scores[s].c[l].c[t].c[p].points = helper_to_calculate_points(player_matches_inner)
                    team_matches_inner = list(set(team_matches_inner + player_matches_inner))
                # print(f"        {team_matches_inner}")
                scores[s].c[l].c[t].points = helper_to_calculate_points(team_matches_inner)
                max.team_matches = list(set(max.team_matches + team_matches_inner))
                league_matches_inner = list(set(league_matches_inner + team_matches_inner))
            # print(f"    {league_matches_inner}")
            scores[s].c[l].points = helper_to_calculate_points(league_matches_inner)
            scores[s].c[l].matched_with = list(set(scores[s].c[l].matched_with + league_matches_inner))
            max.league_matches = list(set(max.league_matches + league_matches_inner))
            sport_matches_inner = list(set(sport_matches_inner + league_matches_inner))
        # print(f"{sport_matches_inner}")
        scores[s].points = helper_to_calculate_points(sport_matches_inner)
        scores[s].matched_with = list(set(scores[s].matched_with + sport_matches_inner))
        max.sport_matches = list(set(max.sport_matches + sport_matches_inner))

    """------Fixing the issue of have multiple things with exact matches (Anthony Davis being on the roster of the Lakers and florida_a&m^rattlers)-----"""
    for npid in certain_matches:
        max_parents_points = list()
        certain_parent_already = False
        for match in certain_matches[npid]:
            s = match[0]
            l = match[1]
            t = match[2]
            #only has sport, league and team.     no player
            p = (match[3] if len(match) == 4 else None)
            #use the leagues points, might want to revert this back to the commented line
            points = scores[s].c[l].points
            # points = (scores[s].c[l].c[t].points if p!=None else scores[s].c[l].points)
            certain_parent = ((scores[s].c[l].certain_match or scores[s].c[l].c[t].certain_match) if p == None else scores[s].c[l].c[t].certain_match)

            if certain_parent and not certain_parent_already:
                certain_parent_already = True
                max_parents_points = [(points, match)]
            elif certain_parent and certain_parent_already:
                max_parents_points.append((points, match))
            elif len(max_parents_points) == 0 or points > max_parents_points[0][0]:
                max_parents_points = [(points, match)]
            elif points == max_parents_points[0][0]:
                max_parents_points.append((points, match))

        if len(max_parents_points) == 1 or certain_parent_already:
            for mpp in max_parents_points:
                s = mpp[1][0]
                l = mpp[1][1]
                t = mpp[1][2]
                p = (mpp[1][3] if len(mpp[1]) == 4 else None)
                p_points = 0
                t_points = 0
                if p != None:
                    scores[s].c[l].c[t].c[p].certain_match = True
                    p_points = helper_to_calculate_points(scores[s].c[l].c[t].c[p].matched_with)
                    scores[s].c[l].c[t].c[p].points += p_points
                    max.player_matches = list(set(max.player_matches + scores[s].c[l].c[t].c[p].matched_with))
                else:
                    t_points = helper_to_calculate_points(scores[s].c[l].c[t].matched_with)
                    max.team_matches = list(set(max.team_matches + scores[s].c[l].c[t].matched_with))
                scores[s].c[l].c[t].certain_match = True
                scores[s].c[l].c[t].points += t_points + p_points
                scores[s].c[l].certain_match = True
                scores[s].c[l].points += t_points + p_points
                scores[s].certain_match = True
                scores[s].points += t_points + p_points

                max.team_matches = list(set(max.team_matches + max.player_matches))
                max.league_matches = list(set(max.league_matches + max.team_matches))
                max.sport_matches = list(set(max.sport_matches + max.league_matches))

    """-----------"""
    max.sport_points = helper_to_calculate_points(max.sport_matches)
    max.league_points = helper_to_calculate_points(max.league_matches)
    max.team_points = helper_to_calculate_points(max.team_matches)
    max.player_points = helper_to_calculate_points(max.player_matches)

    return scores

"""
new implementation of get_roster_matches
"""
def get_matches_initial(np_identifier, np, matches):
    if np_identifier not in matches:
        matches[np_identifier] = dict()
    for sport in master['teams']:
        for league in master['teams'][sport]:
            for team in master['teams'][sport][league]:
                #this is for if you want to differentiate between city/school, teamname/mascott, and if it's a player
                #currently we don't offer different weightings for these so it's commented out

                #n1 = "philadelphia", "alabama", or "kyle mcclatchie"
                #n2 = "eagles", "crimson tide", or "" respectively
                try:
                    n1,n2 = team.split("^")
                except:
                    n1 = team
                    n2 = ""
                n1 = n1.replace("_", " ")
                n2 = n2.replace("_", " ")
                #N = n1.split() + n2.split()

                N = team.replace("_", " ").replace("^", " ")

                #if np in N and N not in matches:
                #this line does the same as above but prevents 'hawks' from matching with 'redhawks'
                if re.search(r"\b" + re.escape(np) + r"\b", N):
                    if N not in matches[np_identifier]:
                        matches[np_identifier][N] = list()
                    #implemented to prevent duplication bug
                    new_team = True
                    for match in matches[np_identifier][N]:
                        if match.sport == sport and match.league == league and match.team == team:
                            new_team = False
                    if new_team:
                        matches[np_identifier][N].append(Match(np_identifier, N, np, s=sport, l=league, t=team, c=n1, m=n2))
                        #matches[N] = (Match(np_identifier, N, np, s=sport, l=league, t=team))

                for player in master['teams'][sport][league][team]['roster']:
                    name = player.replace("_", " ")
                    if re.search(r"\b" + re.escape(np) + r"\b", name):
                        if name not in matches[np_identifier]:
                            matches[np_identifier][name] = list()
                        #implemented to prevent duplication bug
                        new_player = True
                        for match in matches[np_identifier][name]:
                            if match.sport == sport and match.league == league and match.team == team and match.player == player:
                                new_player = False
                        if new_player:
                            matches[np_identifier][name].append(Match(np_identifier, name, np, s=sport, l=league, t=team, c=n1, m=n2, p=player))

    return matches

def get_matches_after_initial(np_identifier, np, matches_all):
    for matches_per_npid in matches_all:
        for match in matches_all[matches_per_npid]:
            if re.search(r"\b" + re.escape(np) + r"\b", match.id):# and s not in matches:
                match.update_match(np)

    return matches_all

"""
layer_nouns aspect

gets called 3 times, for uni, bi and tri
returns a list of matches for each gram for each of the uni, bi, tri

the gram should only be one that has a chance at being a team name or a player name (determined from STOPWORDS)
"""
"""OUTDATED -> replace with get_matches"""
def get_roster_matches(gram):
    matches = []
    for sport in master['teams']:
        for league in master['teams'][sport]:
            for team in master['teams'][sport][league]:
                #n1 = "philadelphia", "alabama", or "kyle mcclatchie"
                #n2 = "eagles", "crimson tide", or "" respectively
                try:
                    n1,n2 = team.split("^")
                except:
                    n1 = team
                    n2 = ""
                n1 = n1.replace("_", " ")
                n2 = n2.replace("_", " ")
                #can only match once for a name at each gram
                if gram.lower() == n1 or gram.lower() == n2 or gram.lower() == (n1 + " " + n2):
                    matches.append((sport, league, team))
                else:
                    for alias in master['teams'][sport][league][team]['alias']:
                        if gram.lower() == alias.replace("_", " "):
                            matches.append((sport, league, team))
                #can match for multiple players, that is why there is no break
                for player in master['teams'][sport][league][team]['roster']:
                    if gram.lower() == player:
                        matches.append((sport, league, team))
    return matches

"""
layer_tfidf aspect

gets called for as many data.json files are within the TFIDF_DATA directory
returns a value for the likelyhood of the term to be a parent of the
news article that came in
"""
def get_probabilities(grams, term):
    #gram_type is the list, either uni, bi, or trigrams
    #print(term) #---->TFIDF_DATA/College_football/data.json for example
    count = 0
    results = dict()
    for gram_type in grams:
        type = nouns[count]
        results[type] = list()
        data = terms[term][type]
        t_pm = 0
        for gram in gram_type:
            UorL = 0
            gram_lower = gram.lower()
            #check if lowercase
            if gram_lower == gram:
                UorL = 1
            try:
                n, p, pm = data[gram_lower][UorL]
            except:
                n = p = pm = 0
            t_pm += pm
            results[type].append((gram, pm))

        count += 1

    """
    for gram_type in results:
        print(gram_type)
        #print(len(results[gram_type]))
        for gram_score in results[gram_type]:
            #print(gram_score)
    """
    return results

#helper function for debugging
def print_matches(matches):
    for gram in matches:
        print(gram[0])
        for match in gram[1]:
            print(match)
        print("\n")

"""
'scores' dict works in the following
'football' : {
    'scores' : [False, [0,0,0]]
    'children' : {
        'ncaa' : {
            'scores' : [False, [0,0,0]]
            "children" : {
                ... for all teams
            }
        }
        'nfl' : {
            'scores' : [0,0,0]
            "children" : {
                ... for all teams
        }
    }
}
for each gram such as 'eagles' or 'philadelphia eagles' each sport, league, and team can only match with it once
so if basketball -> ncaa has 10 hits for 'eagles' because of 'american^eagles', 'boston-college^eagles' ...etc
it will only get a single point for 'eagles' within the basketball->ncaa category as well as the 'basketball'
category (regardless of how many leagues match)
"""
def create_scores_template():
    scores = dict()
    for sport in master['teams']:
        scores[sport] = {"scores" : [False, [[],[],[]]], "children" : dict()}
        for league in master['teams'][sport]:
            scores[sport]['children'][league] = {"scores" : [False, [[],[],[]]], "children" : dict()}
            for team in master['teams'][sport][league]:
                scores[sport]['children'][league]['children'][team] = {"scores" : [False, [[],[],[]]]}

    return scores

def reset_score_check(scores):
    for sport in scores:
        scores[sport]['scores'][0] = False
        for league in scores[sport]['children']:
            scores[sport]['children'][league]['scores'][0] = False
            for team in scores[sport]['children'][league]['children']:
                scores[sport]['children'][league]['children'][team]['scores'][0] = False
    return scores

"""
does the actual scoring for each sport, league and team
"""
#gtsm --> grams_that_should_match
#rd --> ranks_data
def make_sense_of_scores_helper(gtsm, rd):
    scores = [None, None, None]
    """
    this portion gets the score for each gram part (uni, bi, and tri)
    """
    for i in range(len(gtsm)):
        optimal_points = len(gtsm[i])
        gram_points = len(rd[i])
        if optimal_points != 0:
            scores[i] = gram_points/optimal_points

    """
    this portion takes the scores from uni, bi, and tri and converts it to a single score
    """
    gram_weight = [1, 3, 6]
    weight_total = 0
    for i in range(len(scores)):
        if scores[i] == None:
            gram_weight[i] = 0
        weight_total += gram_weight[i]
    score = 0
    for i in range(len(scores)):
        if scores[i] != None:
            score += scores[i]*(gram_weight[i]/weight_total)

    return score

"""
currently only takes the number of matches for each gram and divides it by the number of matches
it should've had if it were a perfect match

DOESN'T TAKE INTO ACCOUNT YET THE FOLLOWING:
- first name matches (i think, maybe I did. have to check on that.)
- nouns that aren't proper nouns that it is still trying to match, but never will since I am only looking at proper nouns in my dictionary (will make all odds lower or unaffected)
- weighting for certain matches (Pat should have a much lower weighting than Philadelphia)
- weighting so that scores of the following [.25, .75, None] won't be 50% (here trigram has no affect since None means it shouldn't have had any matches)
    because I want the odds to be closer to the .75 since bigrams are more signifcant to match than unigrams
- automatic 100% for matching a sport team completely (New York Yankees) (Indicates sport and league and team %100)
    * But not for all things (Kentucky Wildcats. Basketball? Football? Baseball?) (This only indicates NCAA 100%, but not sport too)
- matching allowed past trigrams, since everything is built up to trigrams, teams with names such as (kent state golden flashes) will never be able to have a full match
    * need a way of specifying that it found a full match despite this limitation
- first name matching, but if another field matches a first and last, than the value for the first name decreases
-

MAKE THESE CHANGES IN THE HELPER FUNCTION, WILL NEED TO PASS ANOTHER ARG SPECIFYING THE WEIGHT FOR EACH GRAM (not gram type)
"""
def make_sense_of_scores(scores, grams_that_should_match):
    print("Below are the breakdowns of each of the grams")
    print(f"uni: {grams_that_should_match[0]}")
    print(f" bi: {grams_that_should_match[1]}")
    print(f"tri: {grams_that_should_match[2]}")
    print("-------")
    ranks = copy.deepcopy(scores)

    for sport in ranks:
        ranks[sport]['scores'] = make_sense_of_scores_helper(grams_that_should_match, ranks[sport]['scores'][1])
        for league in ranks[sport]['children']:
            ranks[sport]['children'][league]['scores'] = make_sense_of_scores_helper(grams_that_should_match, ranks[sport]['children'][league]['scores'][1])
            for team in ranks[sport]['children'][league]['children']:
                ranks[sport]['children'][league]['children'][team]['scores'] = make_sense_of_scores_helper(grams_that_should_match, ranks[sport]['children'][league]['children'][team]['scores'][1])
    return ranks

def increment_score(gram, score_data):
    seen_before, all_time_score = score_data
    if not seen_before:
        all_time_score[len(gram.split())-1].append(gram)
        seen_before = True

    return [seen_before, all_time_score]

#as of now, sport/league/team will always have the same max because there are no unique identifiers
#for a sport and league, they rely on team. Player on the other hand has rosters to get points from
def print_max_scores(max):
    print()
    print(f"Sport:  {max.get_sport()}")
    print(f"League: {max.get_league()}")
    print(f"Team:   {max.get_team()}")
    print(f"Player: {max.get_player()}")

def print_scores(scores):
    for s in scores:
        print(f"{s} {scores[s].points} {scores[s].certain_match}")
        for l in scores[s].c:
            print(f"  {l} {scores[s].c[l].points} {scores[s].c[l].certain_match}")
            for t in scores[s].c[l].c:
                print(f"    {t} {scores[s].c[l].c[t].points} {scores[s].c[l].c[t].certain_match}")
        print("\n")

"""
used simply for debugging
"""
def print_ranks(ranks):
    sorted_sports = []
    for sport in ranks:
        sorted_sports.append((sport, ranks[sport]['scores']))
    sorted_sports = sorted(sorted_sports, key = lambda x: x[1], reverse=True)
    for sport in sorted_sports:
        print(float("{:.5f}".format(sport[1])), sport[0])
        sorted_leagues = []
        for league in ranks[sport[0]]['children']:
            sorted_leagues.append((league, ranks[sport[0]]['children'][league]['scores']))
        sorted_leagues = sorted(sorted_leagues, key = lambda x: x[1], reverse=True)
        for league in sorted_leagues:
            print("   " , float("{:.5f}".format(league[1])), league[0])
            sorted_teams = []
            for team in ranks[sport[0]]['children'][league[0]]['children']:
                sorted_teams.append((team, ranks[sport[0]]['children'][league[0]]['children'][team]['scores']))
            sorted_teams = sorted(sorted_teams, key = lambda x: x[1], reverse=True)
            for team in sorted_teams:
                print("       " , float("{:.5f}".format(team[1])), team[0])

"""
not used anymore, phased out and replaced with generate_scores
"""
def get_scores(matches):
    #generates the blueprint to fill in for scoring
    scores = dict()
    for gram, match in matches:
        #print(gram)
        for sport, league, team in match:
            #print(sport, league, team)
            """ CREATES THE DICT PATH IF IT'S BEING SEEN THE FIRST TIME """
            if sport not in scores:
                scores[sport] = {"scores" : [False, [[],[],[]]], "children" : dict()}
            if league not in scores[sport]['children']:
                scores[sport]['children'][league] = {"scores" : [False, [[],[],[]]], "children" : dict()}
            if team not in scores[sport]['children'][league]['children']:
                scores[sport]['children'][league]['children'][team] = {"scores" : [False, [[],[],[]]]}
            """ END OF CREATION PATH  """

            scores[sport]['scores'] = increment_score(gram, scores[sport]['scores'])
            scores[sport]['children'][league]['scores'] = increment_score(gram, scores[sport]['children'][league]['scores'])
            scores[sport]['children'][league]['children'][team]['scores'] = increment_score(gram, scores[sport]['children'][league]['children'][team]['scores'])

        scores = reset_score_check(scores)
    return scores

#called during layer tfidf to get either the uni, bi, or trigam/trigrams
#can be multiple trigrams if the np consisted of a quadgram or more
def get_ubt_grams(np):
    #[['Tom', 'Brady'], ['Tom Brady']]  ------>  'Tom Brady'
    entire = np[len(np)-1][0]
    if len(np) < 3:
        return entire
    #this turns a quadgram+ into a list of trigrams
    else:
        tris = list()
        esplit = entire.split(" ")
        for i in range(len(esplit)-2):
            tri = ""
            for j in range(3):
                tri += esplit[i+j] + " "
            tris.append(tri.strip())
        return tris

def get_percent_makeups(all_np):
    percent_makeups = dict()
    np_probs = dict()
    for np in all_np:
        gtype = None
        #converts all quadgrams+ to a list of trigrams to allow them to be searched here
        ubt_gram = get_ubt_grams(np)
        identifier = ubt_gram

        #if ubt_gram is a list, then it was greater than a trigram
        if type(ubt_gram) is list:
            gtype = 'trigram'
            identifier = " | ".join(ubt_gram)
        else:
            gtype = nouns[len(ubt_gram.split())-1]

        #no sense looking up all the info agian if we've already done it
        if identifier in np_probs:
            np_probs[identifier].seen_again()
            continue
        else:
            #this class stores the NP as well as the sum for the NP across all terms
            #this sum is used in calculating the tfidf
            np_probs[identifier] = ProbNP(identifier)

        #loops through each data.json file within TFIDF_DATA for each uni/bi/tri
        for term in terms:
            """example term: DATA/TFIDF_DATA/basketball/nba/ALL/data.json """
            tsplit = term.split(slash)
            s = tsplit[2]
            l = tsplit[3]
            t = tsplit[4]
            if s not in percent_makeups:
                percent_makeups[s] = Sport(s, 0)
            if l not in percent_makeups[s].c:
                percent_makeups[s].c[l] = League(l, 0)
            if t not in percent_makeups[s].c[l].c:
                percent_makeups[s].c[l].c[t] = Team(t, 0)

            #starting with a number is stored in upper -> index 0 (76ers)
            UorL = 1 #the dictionary holds stats for lowercase in index 1 and upper in 0

            #go through all the trigrams and the one that gives the best percent makeup for each term
            #is the pm it gets assigned
            pm = 0
            if type(ubt_gram) is list:
                max = 0
                for tri in ubt_gram:
                    if tri[0].isupper() or tri[0].isdigit():
                        UorL = 0
                    tri = tri.lower()
                    try:
                        temp = terms[term][gtype][ubt_gram]
                    except:
                        temp = 0
                    if temp > max:
                        max = temp
                pm = max
            #for uni and bigrams
            else:
                if ubt_gram[0].isupper() or ubt_gram[0].isdigit():
                    UorL = 0
                ubt_gram_lower = ubt_gram.lower()
                try:
                    #this is the location that holds the percent makeup for each np for each term
                    pm = terms[term][gtype][ubt_gram_lower][UorL][2]
                except:
                    pm = 0
            np_probs[identifier].increment_sum(pm)
            percent_makeups[s].c[l].c[t].bpnp[identifier] = pm
            if PRINTDEBUG and PRINTDEBUGDEEPER:
                print(s, l, identifier, pm)
    return percent_makeups, np_probs

def apply_tfidf(pm, np_pm_total):
    sport_points = 0
    league_points = 0
    total_points = 0
    for s in pm:
        num_teams = 0
        for l in pm[s].c:
            for t in pm[s].c[l].c:
                for np in np_pm_total:
                    try:
                        pm[s].c[l].c[t].points += (pm[s].c[l].c[t].bpnp[np]/np_pm_total[np].sum) * np_pm_total[np].count
                    #this case happens when the np wasn't seen in anything anywhere, super rare and don't need to do anything
                    except:
                        pass
                pm[s].c[l].points += pm[s].c[l].c[t].points
                pm[s].points += pm[s].c[l].c[t].points
                total_points += pm[s].c[l].c[t].points

            #gets the average score for the league
            pm[s].c[l].points = pm[s].c[l].points/len(pm[s].c[l].c)
            league_points += pm[s].c[l].points
            num_teams += len(pm[s].c[l].c)
        pm[s].points = pm[s].points/num_teams
        sport_points += pm[s].points

    #now run it back to get the percent likelyhood for each sport/league/team
    if total_points == 0:
        for s in pm:
            pm[s].max = 0
            for l in pm[s].c:
                pm[s].c[l].max = 0
                for t in pm[s].c[l].c:
                    pm[s].c[l].c[t].max = 0
    else:
        for s in pm:
            pm[s].max = pm[s].points/sport_points
            for l in pm[s].c:
                pm[s].c[l].max = pm[s].c[l].points/league_points
                for t in pm[s].c[l].c:
                    pm[s].c[l].c[t].max = pm[s].c[l].c[t].points/total_points
    return pm

def print_probs(pm):
    print()
    for s in pm:
        print(f"{s} {pm[s].max}")
        for l in pm[s].c:
            print(f"  {l} {pm[s].c[l].max}")
            for t in pm[s].c[l].c:
                print(f"    {t} {pm[s].c[l].c[t].max}")

def has_a_unique(scores, sport):
    for match in scores[sport].matched_with:
        unique = True
        for s in scores:
            #skip itself
            if s == sport:
                continue
            if match in scores[s].matched_with:
                unique = False
                break
        if unique:
            return True
    return False

#scores, best_matches, and max are all for the layer_search
#probs is for layer_tfidf
def get_tags(scores, best_matches, max, probs):
    tags = list()

    """ AS OF NOW, ONLY CLASSIFY BY SPORT """
    for s in scores:
        if scores[s].certain_match == True:
            tags.append(s)
        else:
            #the sport must have a unique gram in matched with, match with at least 2+ unigrams or bigram+ and be >=75% of the max possible
            # if scores[s].points >= 2*ppg[0] and scores[s].points/max.sport_points >= .75 and (has_a_unique(scores, s)):
            if max.sport_points != 0 and scores[s].points/max.sport_points >= .75 and (has_a_unique(scores, s)):
                tags.append(s)

    #not flushed out completely, use as final resort to tag
    if len(tags) == 0:
        for s in probs:
            if probs[s].max > .3 and s not in tags: #has to be 35% to tag(modify this number to make more accurate)
                tags.append(s)

    if PRINTDEBUG:
        print("--------------------------------------------")
        print(f"SPORT max points:  {max.sport_points}")
        print(f"LEAGUE max points: {max.league_points}")
        print(f"TEAM max points:   {max.team_points}")
        print(f"PLAYER max points: {max.player_points}")
        print_sltp_matched_with(scores)
        # print("--------------------------------------------")
        # print_scores(scores)
        print("--------------------------------------------")
        print_probs(probs)
        print("--------------------------------------------")

    return tags

def get_all_proper_np_from_all_np(all_np):
    all_proper_np = list()
    for sentence in all_np:
        mid = list()
        for np in sentence:
            small = list()
            for each_np in np:
                if each_np not in small and (each_np[0].isupper() or each_np[0].isdigit()):
                    small.append(each_np)
            if small not in mid and len(small) > 0:
                mid.append(small)
        if mid not in all_proper_np and len(mid) > 0:
            all_proper_np.append(mid)

    return all_proper_np

# a decent solution to articles that are all uppercase that uses a large database to determine the probability of a
# word being uppercase or lowercase and makes the correction
def detect_and_correct_all_upper(header):
    parts = re.split(r'\.|!|\?|:', header) #splits on puncutaion
    for part in parts:
        # if len(part) == 0:
            # continue
        words = part.split()
        for word in words:
            try:
                word_data = stopwords[word.lower()]
                val = word_data[1]/word_data[0] #lower to upper ratio
            except:
                val = 0
            # adjust this value as needed to correct the optimal amount of words without destroying correct ones
            if val > 5:
                header = header.replace(word, word.lower())
            # print(f"        {val} {word}")

    return header

def categorize(header, summary):
    header = detect_and_correct_all_upper(header)
    article = header + " " + summary
    content = clean_text(article)
    sentences_tagged = tokenize_content(content)

    #returns a list of noun unigrams, bi and tri from the article
    #grams = do_grams(article)
    #print(grams)
    all_np = list()
    for st in sentences_tagged:
        noun_phrases = generate_noun_phrase_possibilities(st)
        all_np += noun_phrases
    #will use these to searh through the LAYER_SEARCH
    all_proper_np = get_all_proper_np_from_all_np(all_np)

    """("==============LAYER_SEARCH================")"""
    """
    This block involes the layer_search, the direct search in aliases and roster
    """
    matches = dict()
    for np in all_proper_np:
        npid = ''
        for te in np:
            npid += ', '.join(te)
            npid += ', '
        npid = npid[:-2].lower()

        #if the np is [['Atlanta', 'Hawks'], ['Atlanta Hawks']]
        #then uni_np -> ['Atlanta', 'Hawks'] because I want to narrow down the possible matches
        #to the entries that match at least one of the strings in uni_np, and then search through these
        #instead of the entire dictionary
        uni_nps = np[0]
        for subset in uni_nps:
            matches = get_matches_initial(npid, subset.lower(), matches)
        # this expands on the matches that we have already found by updating it with the best it was able to match with
        #for example, given a NP "New England Patriots", we have only matched with the unigram "New" so far, so we will
        #search through the rest of the noun phrase updating our matches with however far it was able to match to
        for j in range(1, len(np)):
            grams = np[j]
            for gram in grams:
                matches[npid] = get_matches_after_initial(npid, gram.lower(), matches[npid])
    best_matches = dict()
    """
    this part removes matches that match with less of the np than other matches
    for example: for the NP "Boston Celtics" with matches "Boston Bruins" and "Boston Celtics",
    it will remove "Boston Bruins" since the celtics matches with more of the np
    """
    for npid in matches:
        if npid not in best_matches:
            best_matches[npid] = TopMatch(npid)
            for matches_per_npid in matches[npid]:
                for match in matches[npid][matches_per_npid]:
                    best_matches[npid].update_best(match)

    # for npid in matches:
    #     if npid not in best_matches:
    #         best_matches[npid] = TopMatch(npid)
    #         for match in matches[npid]:
    #             best_matches[npid].update_best(matches[npid][match])

    #max is a class that all things get a common reference to so that most possible points that could have been
    #scored by a sport/league/team/player are tracked and compared against what was scored
    max = MaxPoints()
    scores = get_certain_match_words(all_np, max)
    scores = generate_scores(best_matches, max, scores)

    # print_max_scores(max)
    # print()
    # print_scores(scores)

    """("==============LAYER_TFIDF================")"""

    #pm is the dictionary that holds raw percent makeup for each team initially
    #then go back through it all again to determine relative probs
    #np_pm_total is a dictionary that each unique np points to the ProbNP class
    #which keeps a count of the sum of percent makeup for any given np across all terms(data.json files)
    pm, np_pm_total = get_percent_makeups(all_np)
    #now each sport/league/team have an assigned probability to them
    probs = apply_tfidf(pm, np_pm_total)

    # print_probs(probs)

    """("==============COMBINE LAYERS================")"""
    tags = get_tags(scores, best_matches, max, probs) #scores changes after this call

    return tags

def main():
    print(categorize("What a wild weekend for the New England Patriots.", "Tom Brady had a massive game throwing the football today."))

if __name__ == "__main__":
    main()
