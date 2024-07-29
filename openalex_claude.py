import requests
import bibtexparser
from PyPDF2 import PdfReader
import json
import html2text
import urllib.request
import io
from bs4 import BeautifulSoup
from collections import deque

def get_paper_data(doi):
    url = f'https://api.openalex.org/works/https://doi.org/{doi}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data for DOI: {doi}")
        return None


# def extract_pdf_content(url):
#     try:
#         response = requests.get(url)
#         if response.status_code == 200:
#             pdf = PdfReader(io.BytesIO(response.content))
#             content = ""
#             for page in pdf.pages:
#                 content += page.extract_text()
#             return content
#     except Exception as e:
#         print(f"Failed to extract PDF content from {url}: {str(e)}")
#     return None


# # def extract_html_content(url):
# #     try:
# #         user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0"

# #         headers={
# #           'User-Agent':user_agent,
# #           'Accept-Encoding': 'gzip, deflate, br, zstd',
# #           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
# #           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
# #           'Accept-Encoding': 'none',
# #           'Accept-Language': 'en-US,en;q=0.8',
# #           'Connection': 'keep-alive'
# #         }
# #         response = requests.get(url, headers=headers)
# #         if response.status_code == 200:
# #             soup = BeautifulSoup(response.content, 'html.parser')
            
# #             # Try to find a PDF link in the HTML
# #             # pdf_link = soup.find('a', href=lambda href: href and href.endswith('.pdf'))
# #             # if pdf_link:
# #             #     pdf_url = pdf_link['href']
# #             #     if not pdf_url.startswith('http'):
# #             #         pdf_url = f"{'/'.join(url.split('/')[:3])}{pdf_url}"
# #             #     return extract_pdf_content(pdf_url)
            
# #             # If no PDF link is found, extract text content from the HTML
# #             article_content = soup.find('div', class_='article-content')
# #             if article_content:
# #                 return article_content.get_text(separator='\n', strip=True)
# #             else:
# #                 return soup.get_text(separator='\n', strip=True)
# #     except Exception as e:
# #         print(f"Failed to extract HTML content from {url}: {str(e)}")
# #     return None

# def extract_html_content(url="https://www.annualreviews.org/content/journals/10.1146/annurev-economics-080614-115430"):
#   user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0"

#   headers={
#     'User-Agent':user_agent,
#     'Accept-Encoding': 'gzip, deflate, br, zstd',
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#     'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
#     'Accept-Encoding': 'none',
#     'Accept-Language': 'en-US,en;q=0.8',
#     'Connection': 'keep-alive'
#   }

#   request = urllib.request.Request(url, None, headers)
#   try:
#       html = urllib.request.urlopen(request).read()
#       html_str = html.decode('utf-8')
#       text = html2text.html2text(html_str)
#       print(text)
#   except urllib.error.HTTPError as e:
#       print(f"HTTP Error {e.code}: {e.reason}")
      

# def extract_content(locations):
#     for location in locations:
#         pdf_url = location.get('pdf_url')
#         landing_page_url = location.get('landing_page_url')
        
#         if landing_page_url:
#             content = extract_html_content(landing_page_url)
#             print("html content: ", content)
#             if content:
#                 return content
            
#         elif pdf_url:
#             content = extract_pdf_content(pdf_url)
#             print("pdf content: ", content)
#             if content:
#                 return content
        
#         # elif landing_page_url:
#         #     content = extract_html_content(landing_page_url)
#             # print("html content: ", content)
#         #     if content:
#         #         return content
        
    
#     return None

def process_paper(paper):
    doi = paper.get('doi')
    if not doi:
        return None

    data = get_paper_data(doi)
    if not data:
        return None

    result = {
        'doi': doi,
        'title': data.get('title'),
        'authors': [author['author']['display_name'] for author in data.get('authorships', [])],
        'abstract': data.get('abstract', []),
        'keywords': data.get('keywords', []),
        'references': data.get('referenced_works', []),
        'metadata': data,
        'level': paper.get('level', 0)
    }

    # # Try to extract full content
    # content = extract_content(data.get('locations', []))
    # if content:
    #     result['full_content'] = content
    # else:
    #     print(f"Could not extract full content for DOI: {doi}")

    return result

def breadth_first_search(seed_papers, max_level=2):
    all_papers_data = []
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
                all_papers_data.append(paper_data)
                
                if level < max_level:
                    for ref_doi in paper_data['references']:
                        if ref_doi not in processed_dois:
                            queue.append(({'doi': ref_doi}, level + 1))

    return all_papers_data

def main():
    with open('seedPapers.bib') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    seed_papers = bib_database.entries

    all_papers_data = breadth_first_search(seed_papers, max_level=1)

    with open('all_papers_data.json', 'w') as outfile:
        json.dump(all_papers_data, outfile, indent=2)

if __name__ == "__main__":
    main()