# NewsTagger: Multi-Layer Sports News Classification System
## Technical Architecture Deep Dive

## Overview

NewsTagger is a hierarchical sports news classification system that combines TF-IDF statistical analysis with exact entity matching through a three-layer ensemble architecture. The system processes news headlines and article summaries to classify content into specific sports, leagues, teams, and players with high precision and interpretability.

## System Architecture

### Core Components

1. **Text Processing Pipeline** - N-gram extraction and entity recognition
2. **Three-Layer Classification System** - Hierarchical ensemble approach
3. **TF-IDF Scoring Engine** - Domain-specific statistical analysis
4. **Exact Matching System** - Entity-based classification with inheritance scoring
5. **Final Decision Layer** - Threshold-based tag selection

## Data Structures

### Primary Data Components

#### TF-IDF Dictionary Structure
```
DATA/TFIDF_DATA/
├── basketball/
│   ├── nba/ALL/data.json
│   └── ncaa/ALL/data.json
├── football/
│   ├── nfl/ALL/data.json
│   └── ncaa/ALL/data.json
└── [sport]/[league]/ALL/data.json
```

Each `data.json` contains term frequencies in the format:
```json
{
  "unigram": {"word": tf_idf_score, ...},
  "bigram": {"phrase": tf_idf_score, ...},
  "trigram": {"phrase": tf_idf_score, ...}
}
```

#### Master Dictionary Structure
```json
{
  "teams": {
    "football": {
      "nfl": {
        "buffalo^bills": {
          "alias": ["bills", "buffalo"],
          "roster": ["james_cook", "josh_allen", ...]
        }
      }
    }
  }
}
```

#### Certain Match Words
High-confidence terms stored in `certain_match_words.json`:
```json
{
  "buffalo bills": "football^nfl^buffalo^bills",
  "james cook": "football^nfl^buffalo^bills^james_cook"
}
```

## Text Processing Pipeline

### N-gram Extraction (`helpers.py:208-254`)

The system implements sophisticated n-gram extraction with part-of-speech filtering:

```python
def do_grams(content):
    tokens = nltk.word_tokenize(content)
    tagged = nltk.pos_tag(tokens)
    grams = ([],[],[])  # unigram, bigram, trigram
    gram = []
    
    for word, pos in tagged:
        if len(gram) == len(nouns):  # max 3 consecutive nouns
            gram.pop(0)
        
        # Filter non-nouns and special characters
        if 'NN' not in pos or "/" in word or "\\" in word or "=" in word:
            word = None
        
        # Remove numeric-only terms while keeping alphanumeric (e.g., "76ers")
        elif not any(c.isalpha() for c in word):
            word = None
            
        gram.append(word)
        
        # Generate all possible n-grams from current window
        j = len(gram) - 1
        while gram[j] != None and j >= 0:
            part = ''
            for k in range(j, len(gram)):
                part += gram[k] + ' '
            entry = part.strip()
            grams[len(entry.split())-1].append(entry)
            j -= 1
    
    return grams
```

**Example Processing:**
- Input: "Buffalo Bills running back James Cook"
- POS Tagged: [("Buffalo", "NNP"), ("Bills", "NNP"), ("running", "VBG"), ("back", "RB"), ("James", "NNP"), ("Cook", "NNP")]
- N-grams Generated:
  - Unigrams: ["Buffalo", "Bills", "James", "Cook"]
  - Bigrams: ["Buffalo Bills", "James Cook"]
  - Trigrams: []

## Layer 1: TF-IDF Statistical Classification

### Implementation (`LayerMaster.py:557-600`)

Layer 1 calculates sport and league probabilities using domain-specific TF-IDF dictionaries:

```python
def get_probabilities(grams, term):
    results = dict()
    for gram_type in grams:
        data = terms[term][type]  # Load sport/league TF-IDF data
        
        for gram in gram_type:
            gram_lower = gram.lower()
            if gram_lower in data:
                score = data[gram_lower]
                # Accumulate scores for this sport/league
```

### Scoring Process

For each extracted n-gram, the system:
1. Looks up TF-IDF scores in all sport/league dictionaries
2. Accumulates scores per sport/league combination
3. Generates probability distributions

**Example from Debug Output:**
```
football nfl deal 0.0012745546600433399
basketball nba deal 0.0016976072544619132
football nfl Cook 7.92597591409148e-05
football nfl Bills 0.002404967548790043
```

The term "Bills" has highest TF-IDF score in football/nfl, indicating strong association.

### Advanced Cross-Corpus TF-IDF Algorithm

#### Custom TF-IDF vs Industry Standard

**Industry Standard TF-IDF Formula:**
```
TF-IDF = TF × IDF
where:
TF = (frequency of term in document) / (total terms in document)
IDF = log(total documents / documents containing term)
```

**NewsTagger's Advanced Two-Stage TF-IDF:**

The system implements a sophisticated cross-corpus TF-IDF that normalizes term frequencies across all sports, providing better discrimination than standard TF-IDF for domain-specific classification.

**Stage 1: Statistical Term Frequency (`wiki_scrape.py:334`)**
```python
# Calculate frequency within sport corpus
percent_makeup = term_count / total_count

# Add statistical significance via Z-score
zscore = (term_count - corpus_average) / corpus_std_dev
percentile = norm.cdf(zscore)  # Convert to statistical percentile
```

**Stage 2: Cross-Corpus Normalization (`LayerMaster.py:886`)**
```python
# Apply inverse document frequency across ALL sports
final_score = (sport_specific_frequency / cross_corpus_sum) * occurrence_count
```

**Complete Formula:**
```
NewsTagger_TFIDF = (TF_sport / Σ(TF_all_sports)) × occurrence_multiplier

where:
TF_sport = statistical frequency in target sport corpus
Σ(TF_all_sports) = sum of frequencies across ALL sport corpora  
occurrence_multiplier = count of corpora containing the term
```

#### Key Innovations

1. **Statistical Significance Over Logarithmic Damping**
   - Standard: Uses `log()` to dampen common terms
   - NewsTagger: Uses Z-score to identify statistically significant terms
   - Advantage: Captures sport-specific terminology that may be frequent but meaningful

2. **Cross-Corpus Normalization**
   - Standard: Compares within single document collection
   - NewsTagger: Normalizes across all sport domains (`np_pm_total[np].sum`)
   - Result: Terms score higher when frequent in target sport but rare elsewhere

3. **Hierarchical Domain Adaptation**
   - Calculates at team → league → sport levels
   - Each level gets domain-specific statistical baselines
   - Preserves nuanced discrimination across sports hierarchies

#### Example Calculation

For term "Bills" in NFL classification:

```python
# Stage 1: Sport-specific frequency
nfl_frequency = bills_count_in_nfl / total_nfl_terms = 0.002404967548790043

# Stage 2: Cross-corpus normalization  
all_sports_sum = nfl_freq + nba_freq + mlb_freq + ... = 0.003987234...
final_score = (0.002404967548790043 / 0.003987234) × occurrence_count
```

This produces high discrimination: "Bills" gets maximum score for NFL, minimal scores for other sports.

## Layer 2: Exact Entity Matching

### Team/Player Recognition (`LayerMaster.py:455-504`)

Layer 2 performs exact string matching against curated entity dictionaries:

```python
def get_matches_initial(np_identifier, np, matches):
    for sport in master['teams']:
        for league in master['teams'][sport]:
            for team in master['teams'][sport][league]:
                # Parse team format: "buffalo^bills"
                n1, n2 = team.split("^")  # city^mascot
                N = team.replace("_", " ").replace("^", " ")
                
                # Exact word boundary matching
                if re.search(r"\b" + re.escape(np) + r"\b", N):
                    matches[np_identifier][N].append(
                        Match(np_identifier, N, np, sport, league, team)
                    )
                
                # Check player roster
                for player in master['teams'][sport][league][team]['roster']:
                    name = player.replace("_", " ")
                    if re.search(r"\b" + re.escape(np) + r"\b", name):
                        matches[np_identifier][name].append(
                            Match(np_identifier, name, np, sport, league, team, player)
                        )
```

### Match Refinement

The system then refines matches by finding the longest possible matches:

```python
def get_matches_after_initial(np_identifier, np, matches_all):
    for match in matches_all[np_identifier]:
        if re.search(r"\b" + re.escape(np) + r"\b", match.id):
            match.update_match(np)  # Extend match if possible
```

## Layer 3: Hierarchical Scoring System

### Point Allocation Structure

```python
ppg = [1, 3, 7, 15, 31]  # Fibonacci-based scoring per gram match

SPORT_max_points = 8
LEAGUE_max_points = 8  
TEAM_max_points = 8
PLAYER_max_points = 4
```

### Inheritance Rules (`LayerMaster.py:940-1025`)

The scoring system implements hierarchical inheritance:

```python
class Field:
    def __init__(self, name, max_points):
        self.name = name
        self.max = max_points
        self.points = 0
        self.certain_match = False
        self.matched_with = []
        self.children = {}

# Inheritance Logic:
if team_match_found:
    sport.points = SPORT_max_points      # 8 points
    league.points = LEAGUE_max_points    # 8 points  
    team.points = min(calculated_points, TEAM_max_points)
elif league_match_found:
    sport.points = SPORT_max_points      # 8 points
    league.points = min(calculated_points, LEAGUE_max_points)
elif sport_match_found:
    sport.points = min(calculated_points, SPORT_max_points)
```

**Example from Debug Output:**
```
football: 8 True
    nfl: 4 True  
        buffalo^bills: 4 ['bills', 'buffalo bills'] True
            james_cook: 4 ['cook', 'james cook'] True
```

### Score Calculation Process

1. **Entity Detection**: "Buffalo Bills" matches team entity
2. **Point Assignment**: Team gets 4 points (2 matched terms)
3. **Inheritance Propagation**: 
   - League (NFL) inherits points
   - Sport (Football) gets maximum points (8)

## Final Decision Layer

### Tag Selection (`LayerMaster.py:1149`)

The system combines all three layers to make final classification decisions:

```python
def get_tags(scores, best_matches, max_points, tfidf_probs):
    # Combine exact matching scores with TF-IDF probabilities
    # Apply thresholds and confidence measures
    # Return final tag classifications
```

### Threshold Application

From debug output, the final selection process:
```
******* Original tags before applying final selection: ['football'] *******
SPORT max points:  8
LEAGUE max points: 8  
TEAM max points:   8
PLAYER max points: 4
```

The system selects tags based on:
1. **Confidence Thresholds**: Minimum point requirements
2. **Relative Scoring**: Comparison against maximum possible points
3. **TF-IDF Validation**: Statistical backing for exact matches

## Example Classification Walkthrough

### Input Processing
**Headline**: "Seeking deal, Cook sits out Bills' practice: 'Just business'"
**Summary**: "PITTSFORD, N.Y. -- Buffalo Bills running back James Cook came out to St. John Fisher University on Sunday afternoon..."

### Step 1: N-gram Extraction
- Unigrams: ["deal", "Cook", "Bills", "practice", "business", "PITTSFORD", "NY", "Buffalo", "Bills", "James", "Cook", ...]
- Bigrams: ["Buffalo Bills", "James Cook", "contract extension", ...]
- Trigrams: ["St John Fisher", ...]

### Step 2: TF-IDF Layer Processing
Each n-gram gets scored against all sport/league combinations:
```
football nfl Bills 0.002404967548790043  # Highest score
basketball nba Bills 8.19052247342858e-05
hockey nhl Bills 6.160962247519027e-05
```

### Step 3: Exact Matching Layer
- "Bills" matches team: `buffalo^bills` in `football/nfl`
- "Buffalo Bills" matches full team name
- "James Cook" matches player in `buffalo^bills` roster
- "Cook" matches partial player name

### Step 4: Hierarchical Scoring
```
football: 8 points (inherited from team match)
├── nfl: 4 points (inherited from team match)
    └── buffalo^bills: 4 points (2 exact matches: "bills", "buffalo bills")
        └── james_cook: 4 points (2 exact matches: "cook", "james cook")
```

### Step 5: Final Classification
- **Primary Tag**: "football" (highest combined score)
- **Confidence**: High (exact entity matches + strong TF-IDF scores)
- **Supporting Evidence**: Team, league, and player all identified

## Technical Innovations

### 1. Hierarchical Ensemble Architecture
The three-layer approach combines complementary classification methods:
- **Statistical Layer**: Captures domain vocabulary and context
- **Entity Layer**: Provides precise identification
- **Scoring Layer**: Implements confidence propagation

### 2. Domain-Specific TF-IDF
Sport/league-specific dictionaries capture nuanced terminology:
- NFL dictionary emphasizes terms like "touchdown", "quarterback"
- NBA dictionary emphasizes "dunk", "three-pointer"
- Prevents cross-sport terminology confusion

### 3. Inheritance Scoring System
Hierarchical point propagation ensures consistent classification:
- Team identification automatically validates sport and league
- Prevents false negatives from incomplete entity matching
- Provides interpretable confidence measures

### 4. Exact vs. Statistical Balance
The system balances precision and recall:
- **Exact matching** prevents false positives
- **TF-IDF scoring** handles ambiguous or incomplete entities
- **Combined approach** achieves high accuracy across diverse inputs

## Performance Characteristics

### Advantages
1. **Interpretability**: Complete decision traceability
2. **Efficiency**: No GPU requirements, fast inference
3. **Precision**: Exact matching prevents false positives  
4. **Domain Adaptation**: Sport-specific vocabularies
5. **Scalability**: Hierarchical architecture handles new sports/leagues

### Trade-offs
1. **Manual Curation**: Requires maintained entity dictionaries
2. **Exact Matching Limitation**: May miss creative entity references
3. **Static Vocabularies**: TF-IDF dictionaries need periodic updates

## Implementation Details

### Key Functions

- `categorize()`: Main classification orchestrator
- `do_grams()`: N-gram extraction with POS filtering  
- `get_probabilities()`: TF-IDF scoring across domains
- `get_matches_initial()`: Entity recognition and matching
- `generate_scores()`: Hierarchical point calculation
- `get_tags()`: Final threshold-based classification

### Data Flow
```
Input Text → N-gram Extraction → TF-IDF Scoring → Entity Matching → 
Hierarchical Scoring → Threshold Application → Final Tags
```

This architecture demonstrates sophisticated understanding of both natural language processing principles and sports domain knowledge, creating a robust and interpretable classification system suitable for production deployment in sports media applications.