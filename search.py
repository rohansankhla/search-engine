import json
import math
import os
import re
import time
# import main
import warnings
from scipy import spatial
from collections import defaultdict
import nltk


def search(query):
    # initializing everything ---------------------
    with open("word_positions.txt") as word_positions:
        word_positions = json.load(word_positions)
    with open("main_index.txt", "r") as main_index:
        ps = nltk.stem.PorterStemmer()
        list_of_dicts = []
        query_tfidf_values = defaultdict(float)
        term_frequency = {}
        query_list = re.findall(r"[\w']+", query)
        query_tfidf_values_list = []
        index_tfidf_values_dict = {}
        docid_cosine_dict = {}
        index_frequency_values_dict = {}

        # making tfidf dictionary for the queries ---------------------
        for term in query_list:
            term = ps.stem(term).lower()
            if term not in term_frequency:
                term_frequency[term] = 1
            else:
                term_frequency[term] += 1
        for term in query_list:
            term = ps.stem(term).lower()
            query_tfidf_values[term] = math.log(((1+len(query_list))/(1+term_frequency[term]) + 1))

        # matching queries ---------------------
        for i in query_list:
            i = ps.stem(i).lower()
            # print(i)
            temp_dict = {}
            temp_list_of_dicts = []
            try:
                main_index.seek(word_positions[i])
                line = main_index.readline()
                temp_dict = json.loads(line)
                temp_list_of_dicts.append(temp_dict)
                list_of_dicts.append(temp_list_of_dicts)
                # print("line:", line)
                # print("temp_dict:", temp_dict)
                # print("temp_list_of_dicts:", temp_list_of_dicts)
                # print("list_of_dicts:", list_of_dicts)
            except KeyError:
                print("No relevant pages found.")

        # building index tfidf values list ---------------------
        for lists in list_of_dicts:
            # print("lists:", lists)
            for dicts in lists:
                # print("dicts:", dicts)
                # print("dicts.values():", dicts.values())
                for postings in dicts.values():
                    for posting in postings:
                        # print("posting:", posting)
                        index_tfidf_values_dict[posting["docid"]] = posting["tf-idf"]
                        index_frequency_values_dict[posting["docid"]] = posting["doc_freq"]

        # print(index_tfidf_values_dict)

        # finding cosine similarity ---------------------
        for k, v in query_tfidf_values.items():
            query_tfidf_values_list.append(v)
        for i in index_tfidf_values_dict:
            # print(index_tfidf_values_dict[i])
            cosine_similarity = 1 - spatial.distance.cosine(query_tfidf_values_list, index_tfidf_values_dict[i])
            docid_cosine_dict[i] = cosine_similarity
        # print(docid_cosine_dict)

        # returning result ---------------------
        # list1 = [each_tuple[0] for each_tuple in sorted(docid_cosine_dict.items(), key=lambda x: x[1], reverse=True)]
        list1 = [each_tuple[0] for each_tuple in sorted(index_tfidf_values_dict.items(), key=lambda x: x[1], reverse=True)]
        return list1[:10]


if __name__ == "__main__":
    print()
    while True:
        q = input("Enter Query: ")

        if q == "Quit":
            break

        start = time.time()
        top_url_list = search(q)
        end = time.time()

        # os.system('cls')

        print("\nTop 10 URLs:")
        print("---------------------------------------")
        with open("url_index.json", "r") as url_index:
            url_dict = json.load(url_index)
            for url, rank in zip([url_dict[str(temp_url)] for temp_url in top_url_list], [i+1 for i in range(10)]):
                print(f"{rank}. {url}")
        print("---------------------------------------")
        print("Type 'Quit' to exit.")

        print("\nTimer: ")
        print(end - start, "seconds")  # timer in seconds
        print()