import json
import bisect
import nltk
import math
import time
import os
import sys
from bs4 import BeautifulSoup
from collections import defaultdict

MAIN_INDEX = defaultdict(list)
URL_INDEX = dict()
TERM_FREQUENCY = dict()
DOCUMENT_FREQUENCY = defaultdict(set)
INDEX_FILE_NAMES = []
WORD_POSITIONS = defaultdict(int)
TOTAL_OFFSET = 0
COUNTER = 0


def read_files():
    global MAIN_INDEX, COUNTER, URL_INDEX, TERM_FREQUENCY, DOCUMENT_FREQUENCY, INDEX_FILE_NAMES, \
        WORD_POSITIONS, TOTAL_OFFSET
    # made a DEV_TEST directory in same directory that DEV is in, containing a small subset of pages
    directory = "[INSERT DRIECTORY PATH / LOCATION HERE]"
    for subdir in os.listdir(directory):
        if subdir != ".DS_Store":
            for file in os.listdir("%s/%s" % (directory, subdir)):
                if os.path.getsize("%s/%s/%s" % (directory, subdir, file)) < 1000000:
                    if COUNTER % 10000 or COUNTER == 0:
                        process_file(directory, subdir, file)
                    else:
                        sort_and_write()
                        process_file(directory, subdir, file)
    sort_and_write()
    merge_indexes()

    # for word, docid_set in DOCUMENT_FREQUENCY.items():
    #     for posting in MAIN_INDEX[word]:
    #         posting["doc_freq"] = len(docid_set)
    #         if posting["term_freq"] > 0:
    #             tfidf = "{:.2f}".format((1 + math.log(posting["term_freq"], 10)) * (math.log((COUNTER+1)
    #                                                                                          /posting["doc_freq"])))
    #         else:
    #             tfidf = 0
    #         posting["tfidf"] = tfidf


def build_index(text, ps):
    global MAIN_INDEX, COUNTER, URL_INDEX, TERM_FREQUENCY, DOCUMENT_FREQUENCY, INDEX_FILE_NAMES, \
        WORD_POSITIONS, TOTAL_OFFSET

    tokens = nltk.word_tokenize(text)
    temp_index = defaultdict(list)
    temp_index.clear()
    start_at = -1

    # indexing ================================================================
    for token in tokens:
        if (token.isalpha() or (token.isalnum() and not token.isdigit()) and len(token) < 7) and (token.isascii()):

            stemmed_token = ps.stem(token.lower())

            if stemmed_token in temp_index:
                temp_index[stemmed_token][0]["position"].append(tokens.index(token, start_at + 1))
                temp_index[stemmed_token][0]["term_freq"] += 1

            else:
                start_at = tokens.index(token)
                temp_index[stemmed_token].append({"docid": COUNTER,
                                                  "position": [start_at],
                                                  "term_freq": 1})
            DOCUMENT_FREQUENCY[stemmed_token].add(COUNTER)

    for word, posting in temp_index.items():
        MAIN_INDEX[word].extend(posting)
    # =========================================================================


def process_file(directory, subdir, file_name):
    global MAIN_INDEX, COUNTER, URL_INDEX, TERM_FREQUENCY, DOCUMENT_FREQUENCY, INDEX_FILE_NAMES, \
        WORD_POSITIONS, TOTAL_OFFSET
    with open("%s/%s/%s" % (directory, subdir, file_name), "r") as f:
        try:
            json_contents = json.load(f)
        except UnicodeDecodeError:
            print("ERROR")
            pass
        ps = nltk.stem.PorterStemmer()
        soup = BeautifulSoup(json_contents["content"], "html.parser")
        URL_INDEX[COUNTER] = json_contents["url"]
        build_index(soup.get_text(), ps)
        for title in soup.find_all('title'):
            try:
                title_tokens = title.get_text().split()
                for token in title_tokens:
                    if (token.isalpha() or (token.isalnum() and not token.isdigit()) and len(token) < 7) and (token.isascii()):
                        stemmed_token = ps.stem(token.lower())
                        # set the last posting's tf-idf to -1
                        try:
                            MAIN_INDEX[stemmed_token][-1]["tf-idf"] = -1   # negative number indicating it is a title
                        except IndexError:
                            MAIN_INDEX[stemmed_token].append({"docid": COUNTER,
                                                              "position": [0],
                                                              "term_freq": 1,
                                                              "doc_freq": 1,
                                                              "tf-idf": -1})

            except TypeError:
                print("error")
                continue

        print(COUNTER)  # Debug - Shows progress of building index
        COUNTER += 1


def sort_and_write():
    global MAIN_INDEX, COUNTER, URL_INDEX, TERM_FREQUENCY, DOCUMENT_FREQUENCY, INDEX_FILE_NAMES, \
        WORD_POSITIONS, TOTAL_OFFSET

    with open(f"main_index{COUNTER}.json", "w") as main_index_file:
        json.dump(dict(sorted(MAIN_INDEX.items())), main_index_file, indent=4)
        INDEX_FILE_NAMES.append(f"main_index{COUNTER}.json")

    MAIN_INDEX.clear()


def merge_indexes():
    global MAIN_INDEX, COUNTER, URL_INDEX, TERM_FREQUENCY, DOCUMENT_FREQUENCY, INDEX_FILE_NAMES, \
        WORD_POSITIONS, TOTAL_OFFSET
    # with ExitStack() as stack:
    #     files = [stack.enter_context(open(fname)) for fname in INDEX_FILE_NAMES]
    #     for file in files:
    #         data = ijson.parse(open(file))
    #         for prefix, event, value in data:

    char_locations = defaultdict(list)
    total_offset = 0
    file_counter = 0
    print(INDEX_FILE_NAMES)
    # This for loop should record index ranges of each starting char of each index
    for fname in INDEX_FILE_NAMES:
        with open(fname, "r") as f:
            keys_list = list(json.load(f).keys())
        start_at = 0
        counter = 0
        previous_word = ''
        try:
            searching_for = keys_list[0][0]
        except IndexError:
            print(keys_list)
            sys.exit()

        for word in keys_list:
            if word[0] != searching_for:
                last_index = counter - 1
                char_locations[searching_for].append([file_counter, start_at, last_index])
                start_at = last_index + 1
                searching_for = word[0]
                counter += 1
                continue
            counter += 1
            previous_word = word

        char_locations[previous_word[0]].append([file_counter, start_at, len(keys_list) - 1])
        file_counter += 1

    for character, recordList in char_locations.items():
        print(character)
        file_counter = 0
        # result of this for loop is MAIN_INDEX having all words starting with particular letter
        for fname in INDEX_FILE_NAMES:
            with open(fname, 'r') as f:
                partial_index_list = list(json.load(f).items())
            for record in recordList:
                docid = record[0]
                # checks to see if docid matches file
                if docid > file_counter:
                    break
                if docid == file_counter:
                    start_at = record[1]
                    end_at = record[2]
                    while start_at != end_at + 1:
                        for posting in partial_index_list[start_at][1]:
                            # inserting posting dict into postings list of appropriate word
                            # bisect.insort(MAIN_INDEX[partial_index_list[start_at][0]], posting, key=lambda x: x["docid"])
                            MAIN_INDEX[partial_index_list[start_at][0]].append(posting)
                        start_at += 1
                    break
            file_counter += 1

        print("second for loop")

        for word, postingsList in MAIN_INDEX.items():
            docid_set = DOCUMENT_FREQUENCY[word]
            docid_set_length = len(docid_set)
            for posting in postingsList:
                posting["doc_freq"] = docid_set_length
                if posting["term_freq"] > 0 and "tf-idf" not in posting:
                    tfidf = float("{:.2f}".format((1 + math.log(posting["term_freq"], 10)) * (math.log((COUNTER + 1)
                                                                                                       / posting[
                                                                                                           "doc_freq"]))))
                elif "tf-idf" in posting:
                    tfidf = -1
                else:
                    tfidf = 0
                posting["tf-idf"] = tfidf

        print("writing to main_index.txt")

        # each time this is reached, MAIN_INDEX has all words that begin with a unique specific letter
        with open(f"main_index.txt", 'a') as main_index_file:
            keys = sorted(list(MAIN_INDEX.keys()))
            word_positions_counter = 0
            # json_string_list = [json.dumps({k: v}) for k, v in MAIN_INDEX.items()]
            for json_str in [json.dumps({k: v}) for k, v in sorted(MAIN_INDEX.items())]:
                json_str_len = len(json_str)
                if TOTAL_OFFSET == 0:
                    WORD_POSITIONS[keys[word_positions_counter]] = 0
                    word_positions_counter += 1
                    TOTAL_OFFSET += json_str_len + 2
                    main_index_file.write(json_str + '\n')
                    continue
                try:
                    WORD_POSITIONS[keys[word_positions_counter]] = TOTAL_OFFSET
                except IndexError:
                    sys.exit()
                TOTAL_OFFSET += json_str_len + 2
                word_positions_counter += 1
                main_index_file.write(json_str + '\n')

        MAIN_INDEX.clear()

    with open(f"word_positions.txt", 'w') as word_positions:
        json.dump(WORD_POSITIONS, word_positions, indent=4)

        # with open(f"index{character}.txt", 'w') as file:
        #     json.dump(dict(sorted(MAIN_INDEX.items())), file)
        #     MAIN_INDEX_NAMES.append(file.name)


if __name__ == "__main__":

    start = time.time()
    read_files()
    end = time.time()

    print("NUMBER OF INDEXED DOCUMENTS:", COUNTER)
    print("NUMBER OF UNIQUE TOKENS:", len(MAIN_INDEX))
    print("SIZE OF INDEX IN KB:", sys.getsizeof(MAIN_INDEX) / 1000)

    print("Timer: ")
    print(end - start)  # timer in seconds
    print()

    with open("url_index.json", "w") as url_index:
        json.dump(URL_INDEX, url_index)

    # main_index: {word: [posting0, posting1, ...], word1: [posting0, posting1, ...], ...}