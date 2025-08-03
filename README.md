# NewsTagger: Advanced Sports News Classification System

A sophisticated hierarchical sports news classification system that combines TF-IDF statistical analysis with exact entity matching to automatically categorize sports articles with high precision and interpretability.

## Quick Start

To see the system in action, run the demo with 10 pre-configured test cases:

```bash
python3 LayerMaster.py
```

This will demonstrate classification across various sports including football, basketball, baseball, soccer, esports, and more.

## How It Works

NewsTagger uses a **three-layer ensemble architecture** to classify sports news:

1. **Layer 1: TF-IDF Statistical Analysis** - Uses domain-specific statistical models trained on sport-specific Wikipedia data
2. **Layer 2: Exact Entity Matching** - Recognizes teams, players, and sports-specific terminology
3. **Layer 3: Hierarchical Scoring** - Combines statistical and entity-based evidence with inheritance scoring

### Basic Usage

```python
from LayerMaster import categorize

# Classify a sports article
headline = "Messi scores stunning free kick in Champions League semifinal"
summary = "Barcelona advances to final after 3-2 aggregate victory"

tags = categorize(headline, summary)
print(tags)  # Output: ['soccer']
```

## Key Features

### Advanced TF-IDF Implementation
- **Cross-corpus normalization** across all sports for better discrimination
- **Statistical significance testing** using Z-scores instead of traditional log scaling
- **Hierarchical domain adaptation** with sport/league/team-specific vocabularies

### Intelligent Entity Recognition
- **Team and player matching** with alias support
- **Hierarchical inheritance scoring** (team match → league confidence → sport classification)
- **Exact boundary matching** to prevent false positives

### Tiered Threshold System
- **Dual-path classification**: Entity-based (preferred) or TF-IDF-only (fallback)
- **Adaptive thresholds**: Higher statistical confidence requires smaller margins
- **False positive prevention** while enabling clear statistical winners

## Architecture Overview

```
Input Text → N-gram Extraction → TF-IDF Scoring → Entity Matching → 
Hierarchical Scoring → Threshold Application → Final Tags
```

For detailed technical documentation, see [`TECHNICAL_ARCHITECTURE.md`](TECHNICAL_ARCHITECTURE.md).

## Data & Training

### Current Data Status (2022)
The system includes pre-trained models and databases from 2022:

- **TF-IDF Models** (`DATA/TFIDF_DATA/`) - Sport-specific statistical models
- **Team Rosters** (`DATA/master_dictionary.json`) - Team and player databases
- **Entity Mappings** (`DATA/certain_match_words.json`) - High-confidence term mappings

**Note**: The demos work well with 2022 data, but classification accuracy would improve with updated rosters and current team information.

### Data Collection Scripts

#### Wikipedia Scraper (`wiki_scrape.py`)
Automatically collects sport-specific vocabulary from Wikipedia:
- Extracts n-grams (unigrams, bigrams, trigrams) from sport pages
- Calculates statistical significance and percentile rankings
- Generates domain-specific TF-IDF models

**Status**: May need updates due to Wikipedia format changes since 2022.

#### Roster Updater (`temp_update_roster.py`) 
Automatically updates team rosters from sports websites:
- Fetches current player rosters for all leagues
- Updates team information and aliases
- Maintains historical backups

**Status**: Likely needs API/scraping logic updates due to website changes since 2022.

## System Requirements

- Python 3.7+
- NLTK for natural language processing
- Required packages: `unidecode`, `json`, `re`, `statistics`