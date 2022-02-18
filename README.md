# Search Engine

This search engine works through scanning a pre-downloaded directory, creating an inverted index of its values, and then
creating individual values for each word and its respective position in a said document.
A large text-based 'dictionary' is built after processing the directory using the main.py file and results in an index
of the docid, position, term frequency, doc frequency, and tf-idf value for each possible query.
Steps:
- Download a directory of urls and insert the path in line 25 of the main.py file
- Run the main.py file and letit create the following files based on the information within the directory:
    - main_index.txt
    - url_index.json
    - word_ppositions.txt
- Once these files have been created, you may use the search.py file to navigate the directory as if you were using a
search engine such as Google.




** Currently only the top 10 urls will appear from a search, but this can be adjusted in line 105 of the search.py file
