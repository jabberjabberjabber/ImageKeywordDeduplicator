import os
from collections import Counter
from typing import Dict, Set, List
from exiftool import ExifToolHelper
from tqdm import tqdm
import inflect
from nltk.corpus import wordnet

# Ensure you've downloaded the required NLTK data
# import nltk
# nltk.download('wordnet')

# Constants
METADATA_FIELDS = ["XMP:Subject", "IPTC:Keywords", "MWG:Keywords", "Keywords"]

# Initialize the inflect engine
p = inflect.engine()

def handle_plurals(word: str) -> str:
    """Convert plural to singular if applicable, otherwise return the original word."""
    singular = p.singular_noun(word)
    return singular if singular else word

def get_synonyms(word: str) -> Set[str]:
    """Get synonyms for a word using WordNet."""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower().replace('_', ' '))
    return synonyms

def extract_keywords(et: ExifToolHelper, file_path: str) -> Set[str]:
    """Extract keywords from image metadata."""
    metadata = et.get_metadata(file_path)[0]
    keywords = set()
    for field in METADATA_FIELDS:
        if field in metadata:
            value = metadata[field]
            if isinstance(value, list):
                keywords.update(value)
            else:
                keywords.add(value)
    return {keyword.lower() for keyword in keywords if keyword}

def process_keywords(all_keywords: List[str]):
    """Process keywords to handle plurals and create synonym groups."""
    # Handle plurals
    singular_keywords = [handle_plurals(keyword.lower()) for keyword in all_keywords]
    
    # Count frequency
    keyword_freq = Counter(singular_keywords)
    
    # Create synonym groups
    synonym_groups = {}
    for keyword in keyword_freq:
        if keyword not in synonym_groups:
            synonyms = get_synonyms(keyword)
            group = [keyword] + [syn for syn in synonyms if syn in keyword_freq]
            main_keyword = max(group, key=lambda x: keyword_freq[x])
            for syn in group:
                synonym_groups[syn] = main_keyword
    
    return keyword_freq, synonym_groups

def update_image_keywords(keywords: Set[str], synonym_groups: Dict[str, str]) -> Set[str]:
    """Update image keywords based on synonym groups."""
    new_keywords = set()
    for keyword in keywords:
        singular = handle_plurals(keyword.lower())
        if singular in synonym_groups:
            new_keywords.add(synonym_groups[singular])
        else:
            new_keywords.add(singular)
    return new_keywords

def process_directory(directory: str) -> Dict[str, Set[str]]:
    """Process all files in the directory and collect updated keywords."""
    file_keywords = {}
    all_keywords = []
    with ExifToolHelper() as et:
        for root, _, files in os.walk(directory):
            for file in tqdm(files, desc="Processing files"):
                file_path = os.path.join(root, file)
                try:
                    keywords = extract_keywords(et, file_path)
                    all_keywords.extend(keywords)
                    file_keywords[file_path] = keywords
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    
    keyword_freq, synonym_groups = process_keywords(all_keywords)
    
    updated_file_keywords = {}
    for file_path, keywords in file_keywords.items():
        updated_keywords = update_image_keywords(keywords, synonym_groups)
        if updated_keywords != keywords:
            updated_file_keywords[file_path] = updated_keywords
    
    return updated_file_keywords

def update_metadata(file_keywords: Dict[str, Set[str]]):
    """Update metadata for all files with updated keywords."""
    with ExifToolHelper() as et:
        for file_path, keywords in tqdm(file_keywords.items(), desc="Updating metadata"):
            keyword_list = list(set(keywords))
            metadata = {
                "XMP:Subject": [],
                "IPTC:Keywords": [],
                "MWG:Keywords": keyword_list,
                "Keywords": []
            }
            try:
                et.set_tags(
                    file_path,
                    tags=metadata,
                    params=["-P", "-overwrite_original"],
                )
            except Exception as e:
                print(f"Error updating metadata for {file_path}: {str(e)}")

def main():
    directory = input("Enter the directory path to process: ")
    
    print("Processing files and updating keywords...")
    updated_file_keywords = process_directory(directory)
    
    print(f"Updating metadata for {len(updated_file_keywords)} files...")
    update_metadata(updated_file_keywords)
    
    print("Keyword standardization and metadata update complete.")

if __name__ == "__main__":
    main()
