Overall:
  When a news article comes in, it contains a header and a summary that needs to be tagged.
  To Tag, call the function categorize with arguments "header" and "summary" that is within the file layermaster.py
  
  layermaster.py - contains the function "categorize(header, summary)" that tags an incoming article. This is what will be called 
    in order to categorize all articles. It returns a list of sports that the article matched with. Almost always just 1 tag, but can be
    multiple or 0 when it was unable to determine or it determined it an article that isn't of interest.
  
  helpers.py     - contains helper functions that layermaster.py and other scripts use
  
  temp_update_roster.py - used to automatically update the rosters of all teams in each of the discussed leagues. 
    To use, go to the main of the script and uncomment "make_hisorical_copy()" in order to make a save copy that 
    gets placed in DATA/master_dictionary_historical/ before any updates are made to DATA/master_dictionary.json.
    Next, to grab the updated roster for a given league, uncomment the 3 lines that are associated with it in function main.
    Ex:
      # master = helpers.open_file(os.path.join(rootdir,'master_dictionary'))
      # master["teams"]["baseball"]["mlb"] = get_baseball_mlb(master["teams"]["baseball"]["mlb"])
      # writefile(master)
    Uncomment these 3 lines in order to update the roster for the MLB
    
  wiki_scrape.py - obtains uni,bi,trigrams from wikipedia articles that are used for tfidf in order to classify articles. 
    Currently set to go to a base page for a league, for instance, NFL goes to the wiki page "NFL" and scans all noun phrases
    into memory as well as travelling to all articles that the base page mentions and repeating. The data is structured as follows
        {"unigram": {"season": [[269, 0.9190703535730449, 0.0006091678631116022], [11066, 1.0, 0.02781897804347061]], 
        "team": [[447, 0.9925072611452742, 0.0010122603524568262] ...
        
        Where "season" is a unigram and was seen uppercased 269 times, fell into the 91st percentile for uppercase words
        and made up .06% of all uppercase unigrams for the dataset of the "NFL". The other information for the unigram 
        "season" is for lowercase
       
    This script also has the ability to automatically gather information for each team as opposed to just the league, but deemed
    not necessary due to size of data accumulated.
    There is no need to run this script for tagging. Only use to get slightly more releavnt data to use.
    
  DATA/TFIDF_DATA/ - this holds all the data accumulated from wiki_scrape.py and is used for the tfidf layer in the 
    article classification
    
  DATA/certain_match_words.json - a list of words that automatically tag a news article with its respective sport/league when available
  
  DATA/master_dictionary.json - holds all team/roster information for each league. Used heavily in article classification and is updated
    with the most recent roster by temp_update_roster.py
    
  DATA/stopwords.json - a large json file that holds the count a word was seen uppercase and lowercase. The database used to accumulate
     these numbers came from scraping millions of sports wiki articles. Used to correct article headers that capitalize all words to 
     improve accuracy of categorization.
    


