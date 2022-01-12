"""
Purpose of this script is to search for a given team on WIKI

#this portion isn't implemented yet
Return: will write to a file 'wiki_not_found.txt' if the wiki article can't be found

Return: or will write to a file 'data.json' in correct pathing that follows, sport, league, team if found
It will write all classified nouns with a count of their lower and upper case as well as percentile and percent makeup
"""

import requests
import nltk
import json
import helpers
import wikipedia
import threading
import statistics
import os
from scipy.stats import norm
# from nltk.corpus import stopwords
#from bs4 import BeautifulSoup
from argparse import ArgumentParser

"""
how data is being formatted
                 UPPER CASE                      lower case
'word':[[count, percentile, % makeup], [count, percentile, % makeup]]
"""
results = {'unigram':dict(), 'bigram':dict(), 'trigram':dict()}
# stop_words = set(stopwords.words('english')) #words like, 'the', 'us'...
nouns = ['unigram', 'bigram', 'trigram']
count = 1
num_urls = 0

#hard coded pages for these sport/league to go to initially
specific_pages = dict()
def add_specfic_pages():
    #these are the keywords that get put into the wikipedia api that get us to their webpages
    specific_pages['fighting|boxing'] = list()
    specific_pages['fighting|boxing'].append("Boxing")
    specific_pages['fighting|boxing'].append("World Boxing Association")
    specific_pages['fighting|ufc'] = list()
    specific_pages['fighting|ufc'].append("Ultimate Fighting Championship")

    specific_pages['tennis|men'] = list()
    #specific_pages['tennis|men'].append("Tennis") CAUSING THE ERROR OF MISEARCHING
    specific_pages['tennis|men'].append("The Championships, Wimbledon")
    specific_pages['tennis|men'].append("The US Open (tennis)")

    specific_pages['baseball|mlb'] = list()
    specific_pages['baseball|mlb'].append("major league baseball")
    specific_pages['baseball|ncaa'] = list()
    specific_pages['baseball|ncaa'].append("college baseball")

    specific_pages['basketball|nba'] = list()
    specific_pages['basketball|nba'].append("national basketball association")
    specific_pages['basketball|ncaa'] = list()
    specific_pages['basketball|ncaa'].append("college basketball")

    specific_pages['football|nfl'] = list()
    specific_pages['football|nfl'].append("nfl")
    specific_pages['football|ncaa'] = list()
    specific_pages['football|ncaa'].append("college football")

    specific_pages['soccer|mls'] = list()
    specific_pages['soccer|mls'].append("major league soccer")
    specific_pages['soccer|epl'] = list()
    specific_pages['soccer|epl'].append("premier league")
    specific_pages['soccer|bundesliga'] = list()
    specific_pages['soccer|bundesliga'].append("Bundesliga")
    specific_pages['soccer|la_liga'] = list()
    specific_pages['soccer|la_liga'].append("La Ligaa")
    specific_pages['soccer|serie_a'] = list()
    specific_pages['soccer|serie_a'].append("Seriee A")
    specific_pages['soccer|ligue_1'] = list()
    specific_pages['soccer|ligue_1'].append("Liguee 1")

    specific_pages['golf|men'] = list()
    specific_pages['golf|men'].append("Golff") #if i don't mispell it, then it searches for "gold"... dumbest fucking bug in the api

    specific_pages['hockey|nhl'] = list()
    specific_pages['hockey|nhl'].append("national hockey league")
    specific_pages['hockey|ncaa'] = list()
    specific_pages['hockey|ncaa'].append("college ice hockey")



add_specfic_pages()


"""
takes word or words from the page (which is word) and adds it to the dictionaries
sub dictionary at 'location' which holds a tuple for each word for the
number of times seen upper and lower-cased
"""
def add_entry(word, location):
    word_lower = word.lower()
    if word_lower not in location:
        location[word_lower] = [[0, None, None], [0, None, None]] #upper, lower counts
    if word_lower == word:
        location[word_lower][1][0] += 1
    else:
        location[word_lower][0][0] += 1
        #results['all'][word_lower][0] += 1

"""
whack shit happens here, nouns that are in sequence with one another (up to a trigram)
get put together and again the counts of upper and lower case are constructed
EXAMPLE: The Phili Eagles' owner, Clint Kershaw is an absolute square at the baseball park.
Groupings: Phili, Eagles, Phili Eagles, owner, ... baseball, park, baseball park
"""
def do_grams(tagged, SOURCE_FOR_DEBUGGING):
    gram = []
    for word, pos in tagged:
        if len(gram) == len(nouns):
            #only care about up to 3 consecutive nouns, so start removing the first one after that
            gram.pop(0)
        if 'NN' not in pos or "/" in word or "\\" in word or "=" in word:
            word = None
        #if the word doesn't contain a single letter, than disregard it
        #intent is to remove shit like 1980, but keep 76ers
        elif not any(c.isalpha() for c in word):
            word = None
        elif len(word) == 1 and (not word.isalpha() and not word.isdigit()):
            word = None
        if word != None and '.' in word:
            #if word starts with '.', get rid of the dot
            if word[0] == '.':
                word = word[1:]
            #gets rid of 'hisory.in december' or 'google.com'
            #keeps the 'H.' in 'Paul H. Walker'
            if not ('.' in word and '.' == word[-1] and len(word.split('.')) == 2):
                word = None
        gram.append(word)
        j=len(gram)-1
        while gram[j] != None and j>=0:
            part = ''
            for k in range(j, len(gram)):
                part += gram[k] + ' '
            entry = part.strip()
            #"Mike" -> unigram, 'Mike Ox' -> bigram

            """
            only 1 of these should be uncommented at a time, depending on if you are debugging
            """
            add_entry(entry, results[nouns[len(entry.split())-1]])
            #add_entry(SOURCE_FOR_DEBUGGING + " " + entry, results[nouns[len(entry.split())-1]])
            """
            """
            j -= 1

def fill_results(content, SOURCE_FOR_DEBUGGING):
    tokens = nltk.word_tokenize(content)
    tagged = nltk.pos_tag(tokens)
    for word, pos in tagged:
        #it's a junk word
        # if word.lower() in stop_words:
        #     continue
        """
        can use to get every single word from an article
        I see no use for it currently so I won't be filling in data for it
        """
    do_grams(tagged, SOURCE_FOR_DEBUGGING)

#adds to the dictionary the incrementation of the number of times
#that a noun was seen upper and lower cased
"""
CURRENTLY UNUSED
"""
def get_noun_counts(content):
    fill_results(content)
    tokens = nltk.word_tokenize(content)
    tagged = nltk.pos_tag(tokens)
    for word, pos in tagged:
        # if word.lower() in stop_words:
        #     continue
        word_lower = word.lower()
        if word_lower not in results['all']:
            results['all'][word_lower] = [0,0] #upper, lower counts
        if word_lower == word:
            results['all'][word_lower][1] += 1
        else:
            results['all'][word_lower][0] += 1
        if 'NN' in pos:
            if word_lower not in results['noun_single']:
                results['noun_single'][word_lower] = [0,0] #upper, lower counts
            if word_lower == word:
                results['noun_single'][word_lower][1] += 1
            else:
                results['noun_single'][word_lower][0] += 1

"""
Return: will write to a file 'wiki_not_found.txt' if the wiki article can't be found -> NOT IMPLEMENTED YET
Return: or will write to a file if found
It will write all classified nouns with a count of their lower and upper case
"""
def get_wiki_content(wiki_page):
    wiki_page = wiki_page.replace('/wiki', '')
    try:
        result = wikipedia.search(wiki_page)
        page = wikipedia.page(result[0])
    except:
        return None

    #title = page.title
    #categories = page.categories
    content = page.content #all text on the wiki page
    #links = page.links
    #summary = page.summary

    return content

def distribute_work_size(num_threads, num_urls):
    return int(num_urls/num_threads), num_urls%num_threads

"""
removes further junk from the wiki article pull, such as the headers
"""
def remove_headers_from_content(content):
    cleaned = list()
    for line in content.split("\n"):
        if len(line) == 0 or (line[0] == '=' and line[len(line)-1] == '='):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)

"""
Each thread will call this function passing it the list of urls
that it is responsible for getting the wiki page of and inputting the
data into the results dict
"""
def get_subpage_content(allocated_urls, wiki_search):

    global count
    global num_urls
    for u in allocated_urls:
        if count % 10 == 0:
            print(f"{wiki_search}: {count} of {num_urls}")
        #print(u)
        try:
            content = get_wiki_content(u)
        except:
            continue
        #the page actually exists
        if content == None:
            count += 1
            continue
        sub_page_content = helpers.replace_accented_letters(content)
        fill_results(remove_headers_from_content(sub_page_content), u)
        count += 1

"""
will calculate each words percentile, and percent makeup of all nouns for upper and lower in relation
to the other nouns in upper and lower
Gets stored in 'results' dictionary and sent to json file
"""
def percentile_and_percent_makeup(location, UoL):
    #coulve just made em send 0 or 1 for upper or lower, but my
    #reasoning at 3 am is that it will make more sense when looking
    #at this later if you send upper or lower to it
    i = 0
    if UoL == 'lower':
        i = 1
    list_sorted = sorted(location.items(), key=lambda x:x[1][i][0])
    list_sorted.reverse() #put it in decreasing order
    count_list = list() #used to get standard deviation
    total_count = 0
    #the purpose for the [1] is to select the value instead of the key
    #because it became a tuple once I converted the dict to a list
    cutoff = 2
    for x in list_sorted:
        val = x[1][i][0]
        #only include words seen at least the desired amount, super bottom heavy and throws off numbers if included
        if val < 2:
            continue
        count_list.append(val)
        total_count += val

    error_present = False
    try:
        average = total_count/len(count_list)
        sd = statistics.stdev(count_list)
    except:
        error_present = True

    #if no words meet the criteria, drop the criteria and just simply do the math on all words
    #the reason a cutoff is implemented is that there are a lot of words only seen once (or whatever
    #the cutoff is set to) so by removing them from the calculations, it makes the good words better
    #at distinguishing the sport
    if error_present:
        count_list = list()
        for x in list_sorted:
            val = x[1][i][0]
            count_list.append(val)
            total_count += 1
    # print("===========")
    # print(count_list)
    # print("===========\n\n")


    """
    inserting the percentile and percent makeup into the 1st and 2nd index of the 3 element tuple
    for either the upper or lower of a word as decided by the 'i'
    """
    for x in list_sorted:
        if error_present or x[1][i][0] < cutoff:
            #for the percentile
            x[1][i][1] = 0
            x[1][i][2] = x[1][i][0]/total_count
        else:
            #print(f"  {x[1][i]}")

            #for the percentile
            try:
                zscore = (x[1][i][0] - average) / sd
                x[1][i][1] = norm.cdf(zscore)
            #sd can be 0, causing an error, if all the values of grams are the same count
            #its super rare but at that point they are all the 50th percentile
            except:
                x[1][i][1] = .5
            #for percent makeup
            x[1][i][2] = x[1][i][0]/total_count


    return dict(list_sorted)

"""
On wiki, teams within the same league are formatted the same in the search engine
IN SUMMARY:
Professional -> City Team
College -> School Mascott <gender> Sport (gender if sport has men's and women's)

    Football:
        NFL:
            City Team (Arizona Cardinals)
        NCAA:
            School Mascott Sport (Navy Midshipmen Football)
            School Mascott Sport (NC State Wolfpack Football)
    Basketball:
        NBA:
            City Team (Philadelphia 76ers)
        NCAA (men):
            School Mascott Gender Sport (Duke Blue Devils men's basketball)
            School Mascott Gender Sport (Indiana Hoosiers men's basketball)
        NCAA (women):
            School Mascott Gender Sport (Indiana Hoosiers women's basketball)
    Baseball:
        MLB:
            City Team (Philadelphia Phillies)
        NCAA:
            School Mascott Gender Sport (Vanderbilt Commodores baseball)
    And so on
"""
def dict_team_2_wiki_team(sport, league, team):
    wiki_search = team.replace("^", " ").replace("_", " ")
    if league == 'ncaa':
        if sport != "football":
            wiki_search += " men's"
        wiki_search += " " + sport
    return wiki_search

"""
appends and returns selected indicies to a list user input '1,2-5, 7' -> [1,2,3,4,5,7]
"""
def get_selection_indicies():
    print("selection: ", end='')

    fields = input().replace(" ", "").split(",")

    if fields[0].lower() == 'a':
        return 'a'
    chosen = []
    for field in fields:
        if "-" in field:
            lower,upper = field.split("-")
            for i in range(int(lower), int(upper)+1):
                chosen.append(i)
        else:
            chosen.append(int(field))
    return chosen

"""
asks the user what sport/league/team they want to update the database for from wiki
"""
def get_selections(sltp, selections, sport=None, league=None):
    os.system('cls' if os.name == 'nt' else 'clear')

    try:
        #line below won't cause error for sports like UFC where I want to go to a specific page on wiki
        specific_pages[sport+"|"+league]
        if sport not in selections:
            selections[sport] = dict()
        if league not in selections[sport]:
            selections[sport][league] = dict()

        selections[sport][league] = specific_pages[sport+"|"+league]
    except:
        print("Input 'a' to choose all")
        print("To select 1 through 10 inclusive, 12, and 44 through 56 do the following")
        print("1-10, 12, 44-56")
        print("==================================================")
        i = 1
        for field in sltp:
            print(f"{i}: {field.replace('_', ' ').replace('^', ' ')}")
            i += 1
        chosen = get_selection_indicies()

        if chosen == 'a':
            chosen = []
            for x in range(1, i):
                chosen.append(x)

        i = 1
        for field in sltp:
            #could make slightly more efficient by using a sorted stack and popping
            #but it would have meaningless increase on performance, so we'll just keep it more simple
            #print(chosen)
            if i not in chosen:
                i += 1
                continue
            #print(field)
            if sport==None:
                selections[field] = dict()
            else:
                if league==None:
                    selections[sport][field] = dict()
                else:
                    selections[sport][league][field] = dict()
            i += 1

    return selections

def do_work(num_threads, urls, path, file_name, wiki_search):
    global results
    global count
    global num_urls
    count = 1
    results = {'unigram':dict(), 'bigram':dict(), 'trigram':dict()}
    num_urls = len(urls)
    #decides how many links each thread will handle
    allocation_size, leftover = distribute_work_size(num_threads, num_urls)
    #print(allocation_size, leftover)
    print(f"Pulling data from first article of {num_urls} for {wiki_search}\n\n")
    all_threads = list()
    for i in range(num_threads):
        val = allocation_size
        if leftover != 0:
            val += 1
            leftover -= 1
        #the extra set of brackets arount the urls[:val] part is to counter the args
        #decapsulation process, which would strip the aspect of it being a list and
        #instead would send each element as its own arguement
        thread = threading.Thread(target=get_subpage_content, args=([urls[:val], wiki_search]))
        thread.start()
        all_threads.append(thread)
        urls = urls[val:]

    #wait for all threads to finish before continuing execution
    for i in range(num_threads):
        all_threads[i].join()

    print("---Finished pulling data")
    print("---Begining percentile and probability calculations for each word")
    #quit()
    for kind in results:
        results[kind] = percentile_and_percent_makeup(results[kind], 'upper')
        results[kind] = percentile_and_percent_makeup(results[kind], 'lower')
    helpers.make_historical_copy(path, file_name)
    helpers.write_json_to_file(path+file_name, results, False)
    print("---Wrote data to file successfully\n")

def main(num_threads):
    master = helpers.open_file(os.path.join("DATA", "master_dictionary.json"))
    sltp = master['teams']
    base_path = os.path.join("DATA", "TFIDF_DATA", "")
    file_name = 'data.json'

    selections = get_selections(sltp, dict())
    #leagues
    for sport in selections:
        selections = get_selections(sltp[sport], selections, sport)
        for league in selections[sport]:
            selections = get_selections(sltp[sport][league], selections, sport, league)

    os.system('cls' if os.name == 'nt' else 'clear')

    failed_pages = []
    print("********************************************")
    print(f"STATUS: Executing program on {num_threads} thread(s).\nUse -t to specify number of threads.")
    print("********************************************")
    for sport in selections:
        for league in selections[sport]:
            #sports with teams
            if type(selections[sport][league]) is dict:
                for team in selections[sport][league]:
                    path = base_path + sport + "/" + league + "/" + team + "/"
                    check = helpers.isPath(path + "/" + file_name)

                    if check.is_file():
                        p = path.split("/")
                        p = " ".join(p[1:]).replace("^", " ").replace("_", " ")
                        print(f"--->ALREADY EXISTS, skipping: {p}\n")
                        continue
                    wiki_search = dict_team_2_wiki_team(sport, league, team)
                    #print(team)        #atlanta^braves
                    #print(team_path)   #LOOKUPS/baseball/mlb/atlanta^braves/
                    #print(wiki_search) #atlanta braves
                    print(wiki_search)
                    try:
                        urls = (wikipedia.page(wiki_search)).links
                    except:
                        failed_pages.append(f"{sport} {league} {team} -> {wiki_search}")
                        continue
                    urls.insert(0,wiki_search)

                    do_work(num_threads, urls, path, file_name, wiki_search)
                    #print(len(urls))

            #individual sports (fighting, tennis, ...)
            else:
                path = base_path + sport + "/" + league + "/" + "ALL" + "/"
                check = helpers.isPath(path + "/" + file_name)
                if check.is_file():
                    p = path.split("/")
                    p = " ".join(p[1:]).replace("^", " ").replace("_", " ")
                    print(f"--->ALREADY EXISTS, skipping: {p}\n")
                    continue
                """ Gets all the pages and their reference pages to go to for the hard coded pages to go to """
                urlsorg = list()
                for page in selections[sport][league]:
                    page_urls = wikipedia.page(page).links
                    print(wikipedia.page(page).title)
                    urlsorg += page_urls
                    urlsorg.insert(0,page)
                urls = list()
                for u in urlsorg:
                    if u not in urls:
                        urls.append(u)
                """ Ends this portion ::: now I have the urls """

                do_work(num_threads, urls, path, file_name, sport+" "+league)


    failpath = 'FAILED/FAILED.txt'
    helpers.make_historical_copy(base_path+"FAILED/", "FAILED.txt") #returns True if a file exists to be saved to historical, false otherwise
    prev = list()
    try:
        with open(f'{base_path}{failpath}', 'r') as the_file:
            for line in the_file:
                linesplit = line.split()
                s = linesplit[0]
                l = linesplit[1]
                t = linesplit[2]
                #only keep the historical failures if a file for them still doesn't exsit
                try:
                    f = open(f"{base_path}{s}/{l}/{t}/data.json")
                    f.close()
                except:
                    ll = line.strip()
                    if ll not in failed_pages:
                        prev.append(ll)
    except:
        pass
    bad_pages = failed_pages + prev
    bad_pages.sort()
    with open(f'{base_path}{failpath}', 'w') as the_file:
        for bad_page in bad_pages:
            the_file.write(bad_page + '\n')

    print("NOTE: View all failed searches at the relative file pathing 'TFIDF_DATA/FAILED/FAILED.txt'")


if __name__ == "__main__":
    #can run from 1 to 8 threads, if none are specified will only run on 1 thread
    parser = ArgumentParser()
    parser.add_argument('-t', '--threads', help='threads help', default=1, type=int, choices=range(1,9))
    args = parser.parse_args()
    main(args.threads)
