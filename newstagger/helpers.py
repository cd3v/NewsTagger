import unidecode
import json
import shutil
import os.path
import unidecode
import nltk

from pathlib import Path
from datetime import datetime
from nltk.corpus import stopwords


"""
***********************************************
keep this file in the same directory as whatever scripts are using it
***********************************************
"""

stop_words = set(stopwords.words('english')) #words like, 'the', 'us'...
#nouns isn't used for index to dictionary like it is in wiki_scrape_href to
#get to the correct dictionary, but to keep things consistent I am using the
#len(nouns) instead of simply saying 3
nouns = ['unigram', 'bigram', 'trigram']

"""
takes in content, either as a single sentence or an entire paragragh+
returns a list of sentences where each word is tagged as its part of speech
"""
def tokenize_content(content):
    sentences_tagged = list()
    sentences = nltk.sent_tokenize(content)
    for sentence in sentences:
        tokens = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)
        sentences_tagged.append(tagged)
    return sentences_tagged

"""
takes a line from feedly and formats it to imporve accuracy
if the line only contains capital words, dont use it since it makes detecting NNP harder
in this case ill just return an empty string

currently does ryan-herrara -> ryanherrara, maybe look into this if there are problems
"""
#helper function that takes a single string and resturns the string after making capable for processing
def clean_line(line):
    #makes accented letters become letters from english alphabet
    line = unidecode.unidecode(line)
    line = line.split()
    word = 0
    all_uppcase = True
    while word < len(line):
        #BEFORE: Matthew Dever's jumpshot is worse the Pirates' Corey Smith
        #AFTER: Matthew Dever jumpshot is worse the Pirates Corey Smith
        line[word] = line[word].replace("'s", "").replace("’s", "").replace("'", "")
        corrected_word = list()
        letter = 0
        while letter < len(line[word]):
            if line[word][letter].isalpha() or line[word][letter].lower().isalpha():
                corrected_word.append(line[word][letter])
            letter += 1
        line[word] = ''.join(corrected_word)
        word += 1

    return ' '.join(line)

def isPath(f):
    return Path(f)

"""
takes in the following
[('Atlanta', 'NNP'), ('Hawks', 'NNP'), ('take', 'VB'), ('lead', 'NN'), ('in', 'IN'), ('series', 'NN'), ('against', 'IN'), ('Tom', 'NNP'), ('Brady', 'NNP'), ('from', 'IN'), ('Kent', 'NNP'), ('State', 'NNP'), ('Golden', 'NNP'), ('Flashes', 'NNP'), ('.', '.')]

returns a list of the following
[['Atlanta Hawks'], ['Atlanta', 'Hawks']]
[['lead']]
[['series']]
[['Tom Brady'], ['Tom', 'Brady']]
[['Kent State Golden Flashes'], ['Kent State Golden', 'State Golden Flashes'], ['Kent State', 'State Golden', 'Golden Flashes'], ['Kent', 'State', 'Golden', 'Flashes']]
"""
def generate_noun_phrase_possibilities(tagged_sentence):
    noun_phrases = list()
    current_noun_phrase = list()

    i = 0
    while True:
        if i >= len(tagged_sentence):
            break
        word = tagged_sentence[i][0]
        pos = tagged_sentence[i][1]

        if 'NN' not in pos:
            if word[0].isdigit() and any(c.isalpha() for c in word):
                pass
            else:
                word = None

        if word == None or "/" in word or "\\" in word or "=" in word:
            word = None
        elif not any(c.isalpha() for c in word):
            word = None
        elif len(word) == 1 and (not word.isalpha() and not word.isdigit()):
            word = None

        if word != None and '.' in word:
            # #if word starts with '.', get rid of the dot
            # if word[0] == '.':
            #     word = word[1:]
            # #gets rid of 'hisory.in december' or 'google.com'
            # #keeps the 'H.' in 'Paul H. Walker'
            # if not ('.' in word and '.' == word[-1] and len(word.split('.')) == 2):
            #     word = None
            word = word.replace(".", "")
        if word != None:
            if len(current_noun_phrase) != 0:
                #previous words starting letter
                pw = current_noun_phrase[len(current_noun_phrase)-1][0]
                cur = word[0]
                #This is for the case of ('Miami', 'NNP'), ('opener', 'NN') which we want to be separate things
                if (pw.isupper() and cur.islower()) or (pw.isdigit() and cur.islower()) or (pw.islower() and cur.isupper()) or (pw.islower() and cur.isdigit()):
                    tagged_sentence.insert(i+1, (word, pos))
                    word = None
                #the noun phrase is still going
                else:
                    current_noun_phrase.append(word)
            #the noun phrase is still going
            else:
                current_noun_phrase.append(word)
        #an existing noun phrase ended
        if len(current_noun_phrase) != 0 and (word == None or i == len(tagged_sentence)-1):
            #number of words in the noun phrase
            num_words = len(current_noun_phrase)
            noun_phrases_listed = list()
            noun_phrases_listed.append(current_noun_phrase)
            for window in range(1,num_words):
                noun_phrases_listed.append(list())
                for start in range(num_words-window):
                    inner_phrase = ''
                    for noun in range(start, start+window+1):
                        inner_phrase += current_noun_phrase[noun] + ' '
                    inner_phrase = inner_phrase.strip()
                    noun_phrases_listed[len(noun_phrases_listed)-1].append(inner_phrase)
            #noun_phrases_listed.reverse()
            noun_phrases.append(noun_phrases_listed)
            current_noun_phrase = list()
        i+=1
    return noun_phrases


# Opening JSON file
def open_file(filename):
    if '.json' in filename or '.txt' in filename:
        with open(filename) as json_file:
            return json.load(json_file)
    else:
        with open(filename+'.json') as json_file:
            return json.load(json_file)

"""
given a file path, if it doesn't exist, make it
this is used when I try to create and write to a file that doesn't exist
"""
def make_path_if_not_exist(folders):
    chain = ''
    for folder in folders:
        chain += folder + '/'
        if not os.path.exists(chain):
            os.makedirs(chain)

"""
does as the name says, also alphabatizes it
"""
def write_json_to_file(filename, data, do_sort):
    folders = filename.split("/")[:-1] #remove the .json file part at the end
    make_path_if_not_exist(folders)
    with open(filename, "w") as outfile:
        json.dump(data, outfile, sort_keys=do_sort)

"""
this will also make the directories if it doesn't exist
"""
def make_historical_copy(base_dir, file_name):
    make_path_if_not_exist((base_dir + 'historical').split("/"))
    now = datetime.now()
    now = str(now).replace(' ', '-').replace(':', '-').split('.')[0]
    #shutil.copyfile('betting_dictionaries.py', f'Dictionary_Historical//{now}.py')
    file_2_be_replaced = f'{base_dir}{file_name}'
    if os.path.isfile(file_2_be_replaced):
        shutil.copyfile(file_2_be_replaced, f'{base_dir}historical/{now}')
        return True
    else:
        return False
"""
**********DO LATER***********
currently I have a clean_line function, but i forget what uses it, soooooooo
intent of this one is to have a single function I call to perform all the cleaning I need
"""
def clean_text(content):
    return replace_accented_letters(content)
"""
this is for when you see names with accents, it converts it
to the letter without the accent since decodings often fuck it
up and it could look something like espa\u00f1ol for espanol (with the accent on the n)
"""
def replace_accented_letters(content):
    return unidecode.unidecode(content)

def do_grams(content):
    tokens = nltk.word_tokenize(content)
    tagged = nltk.pos_tag(tokens)
    grams = ([],[],[]) #will hold 'unigram', bi and tri
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
        """ POTENTIALLY implement if you see an issue with common words sneaking into dataset
        elif word in stop_words:
            word = None
        """
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
            grams[len(entry.split())-1].append(entry)
            #add_entry(entry, results[nouns[len(entry.split())-1]])
            #add_entry(SOURCE_FOR_DEBUGGING + " " + entry, results[nouns[len(entry.split())-1]])
            j -= 1
    return grams
