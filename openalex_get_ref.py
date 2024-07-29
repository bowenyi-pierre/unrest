import requests
import bibtexparser
import json
from collections import deque

def get_paper_data(doi):
    url = f'https://api.openalex.org/works/https://doi.org/{doi}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data for DOI: {doi}")
        return None


def reconstruct_abstract(inverted_index):
    """
    Reconstruct the original abstract from the inverted index.
    """
    if not inverted_index:
        return ''
    
    max_index = max(max(indices) for indices in inverted_index.values())
    
    words = [''] * (max_index + 1)
    
    for word, indices in inverted_index.items():
        for index in indices:
            words[index] = word
    
    return ' '.join(words).strip()


def get_clean_keywords(keywords):
    """
    Get a list of keywords from the keywords list.
    """
    if not keywords:
        return []
    
    return [keyword['display_name'] for keyword in keywords]
    

def process_paper(paper):
    doi = paper.get('doi')
    if not doi:
        return None

    data = get_paper_data(doi)
    if not data:
        return None
    
    abstract_inverted_index = data.get('abstract_inverted_index')
    keywords = data.get('keywords')
        
    result = {
        'abstract': reconstruct_abstract(abstract_inverted_index),
        'keywords': get_clean_keywords(keywords),
        'references': data.get('referenced_works', []),
        'level': paper.get('level', 0),
        'metadata': data,
    }

    return result

def breadth_first_search(seed_papers, max_level=2):
    all_papers_data = []
    no_data_dois = set()
    processed_dois = set()
    queue = deque([(paper, 0) for paper in seed_papers])

    while queue:
        current_paper, level = queue.popleft()
        
        if level > max_level:
            continue

        doi = current_paper.get('doi')
        if doi and doi not in processed_dois:
            processed_dois.add(doi)
            current_paper['level'] = level
            paper_data = process_paper(current_paper)
            
            if paper_data:
                # print("Hi")
                all_papers_data.append(paper_data)
                
                if level < max_level:
                    for ref_doi in paper_data['references']:
                        if ref_doi not in processed_dois:
                            queue.append(({'doi': ref_doi}, level + 1))
            else:
                no_data_dois.add(doi)
    print(f"No data for {len(no_data_dois)} DOIs, including:{no_data_dois}")
    return all_papers_data

def main():
    with open('seedPapers.bib') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    seed_papers = bib_database.entries

    all_papers_data = breadth_first_search(seed_papers, max_level=1)

    with open('papers_data.json', 'w') as outfile:
        json.dump(all_papers_data, outfile, indent=2)

if __name__ == "__main__":
    main()