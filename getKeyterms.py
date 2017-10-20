import os
import pymarc
from collections import Counter
import pickle
from nltk.tokenize import word_tokenize
import time
file_name = "norart20170906.xml"
full_file = os.path.abspath(os.path.join('data',file_name))

nokkelord = []
nokkelord_og_dewey = {}
deweyarray = []

def get_articles(original_name):
    # Tar inn en textfil som er labelet på fasttext-format. Gir ut to arrays. Et med deweys og et med tekstene. [deweys],[texts]
    articles=open(original_name+'.txt',"r")
    articles=articles.readlines()
    dewey_array = []
    docs = []
    dewey_dict = {}
    for article in articles:
        dewey=article.partition(' ')[0].replace("__label__","")
        article_label_removed = article.replace("__label__"+dewey,"")
        docs.append(article_label_removed)
        dewey_array.append(dewey)

    return dewey_array, docs


def make_dewey_keyword_dict():
    with open(full_file, 'rb') as fh:
        for record in pymarc.parse_xml_to_array(fh):
            if "245" in record and "082" in record and "650" in record:

                if "a" in record["082"] and "a" in record["650"]:
                    deweynr = record['082']['a'].replace(".", "")
                    deweynr = deweynr.replace("-", "")
                    deweynr = deweynr[:3]

                    key_term = record["650"]["a"]
                    deweyarray.append(deweynr)
                    nokkelord.append(key_term)
                    if deweynr[:3] not in nokkelord_og_dewey:
                        nokkelord_og_dewey[deweynr]=[key_term]
                    else :
                        if key_term not in nokkelord_og_dewey[deweynr]:
                            nokkelord_og_dewey[deweynr].append(key_term)


    print(nokkelord_og_dewey)
    print(len(nokkelord_og_dewey))
    print(len(set(deweyarray)))

    return nokkelord_og_dewey,nokkelord, deweyarray

def get_keyword_frequency(array_with_keywords):
    return Counter(nokkelord)
#Writing terms that are unique for each dewey to file
def write_only_unique_terms_to_dewey(dict_with_dewey_and_keywords, dict_with_keyword_and_frequencies):
    onlyUniqueTermsPerDeweyDict = {}
    uniqueKeywords = []
    if not os.path.exists("terms_per_dewey"):
        os.makedirs("terms_per_dewey")

    for dewey,keyword in dict_with_dewey_and_keywords.items():
        term_file = open("terms_per_dewey/"+str(dewey)+".txt", "w")
        for term in keyword:
            if dict_with_keyword_and_frequencies[term]==1:
                term_file.write(term + '\n')
                uniqueKeywords.append(term)
                if dewey not in onlyUniqueTermsPerDeweyDict:
                    onlyUniqueTermsPerDeweyDict[dewey] = [term]
                else:
                    onlyUniqueTermsPerDeweyDict[dewey].append(term)

        term_file.close()
    return onlyUniqueTermsPerDeweyDict, uniqueKeywords

def tokenizeText(text):
    tokenizedText = word_tokenize(text, language="norwegian")
    return tokenizedText
def isAnyKeywordsInText(tokenizedText, list_of_keywords):
    return any(i in tokenizedText for i in list_of_keywords)
def findWhichKeyWordsAreInText(tokenizedText, list_of_keywords):
    return list(set(tokenizedText).intersection(list_of_keywords))
def whichDeweyDoesTheKeywordBelongTo(keywords_from_text, dict_containing_keywords_and_deweys):
    inv_dictionary = {}
    for key, value in dict_containing_keywords_and_deweys.items():

        for terminator in value:
            inv_dictionary.setdefault(terminator, []).append(key)

    dewey_corresponding_to_keyword = []

    for keywordInText in keywords_from_text:
         dewey_corresponding_to_keyword.append(inv_dictionary[keywordInText])

    dewey_corresponding_to_keyword = [item for sublist in dewey_corresponding_to_keyword for item in sublist]
    return dewey_corresponding_to_keyword

if __name__ == '__main__':
    # nokkelord_og_dewey, nokkelord, deweyarray = make_dewey_keyword_dict()
    # with open("keywordDict.pickle", "wb") as handle:
    #     pickle.dump([nokkelord_og_dewey,nokkelord,deweyarray], handle, protocol = pickle.HIGHEST_PROTOCOL)

    with open("keywordDict.pickle", "rb") as handle:
        KeywordPickle = pickle.load(handle)
    nokkelord_og_dewey = KeywordPickle[0]
    nokkelord = KeywordPickle[1]
    deweyarray = KeywordPickle[2]

    keyword_frequencies = get_keyword_frequency(nokkelord)
    uniqueTermsDict, uniqueKeywords = write_only_unique_terms_to_dewey(nokkelord_og_dewey, keyword_frequencies)
    print(len(uniqueTermsDict))

    deweyarray,docs = get_articles("tekst/combined3deweys")
    recog_results = []
    i = 0
    ingen_keywords = 0
    isInResultDictionary = 0;
    #dewey_correct = []
    for tekst in docs:
        tokenizedText = tokenizeText(tekst)

        keyWordBool = isAnyKeywordsInText(tokenizedText,uniqueKeywords)

        if keyWordBool:
            print("Et nøkkelord finnes i teksten, fortsetter prosessen")

            keywordsInText = findWhichKeyWordsAreInText(tokenizedText, uniqueKeywords)

            result = Counter(whichDeweyDoesTheKeywordBelongTo(keywordsInText, uniqueTermsDict))
            if deweyarray[i] == result[deweyarray[i]]:
                isInResultDictionary = isInResultDictionary + 1
            #print(str(deweyarray[i]) + " " + str(result))

        else:
            print("Ingen nøkkelord finnes i teksten. Prosessen stoppes.")
            ingen_keywords = ingen_keywords + 1
        i = i + 1
        #time.sleep(2)
    print("Totalt antall:" + str(i) + '\n' + "Antall der riktig dewey var nevnt:"+str(isInResultDictionary) + '\n'
            + "Hadde ikke nøkkelord:" + str(ingen_keywords))