""" Scraper for Verbix.com """

import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

OPTIONS = Options()
OPTIONS.headless = True
EXEC_PATH = ".local/share/Anki2/addons21/german_anki/geckodriver"
DRIVER = webdriver.Firefox(options=OPTIONS, executable_path=EXEC_PATH)

URL = """http://verbix.com/webverbix/German/{0}.html"""

def scrape_verbix(verb):
    """ Gets conjugated forms of a german verb """
    DRIVER.get(URL.format(verb))
    time.sleep(0.3)

    soup = BeautifulSoup(DRIVER.page_source, 'lxml')

    verb_conj = {}

    present_table = get_conjugation_table(soup, "Indicative", "Present")

    """ Checking for seperable prefix """
    if len(present_table["ich"].split(";")[0].split(" ")) > 1:
        verb_conj['prefix'] = present_table["ich"].split(";")[0].split(" ")[1]

    """ Parsing present tense """
    for pronoun in present_table:
        present_table[pronoun] = present_table[pronoun].split(";")[0].split(" ")[0] # stripping prefix

    for pronoun in ["ich", "du", "er;sie;es", "ihr", "wir"]:
        verb_conj[pronoun] = present_table[pronoun]

    """ Parsing past participle and auxillary verb"""

    perfect_table = get_conjugation_table(soup, "Indicative", "Perfect")

    [aux_verb, pp] = perfect_table['wir'].split(";")[0].split(" ")

    if aux_verb == "sind":
        aux_verb = "sein"

    verb_conj['aux_verb'] = aux_verb
    verb_conj['past_participle'] = pp

    """ Parsing imperfect tense """

    imperfect_table = get_conjugation_table(soup, "Indicative", "Past")

    verb_conj['imperfect'] = imperfect_table['ich'].split(";")[0].split(" ")[0]

    """ Parsing konjunctiv voice """

    konjunctiv_table = get_conjugation_table(soup, "Conjunctive I and II", "Past")

    verb_conj['konjunctiv'] = konjunctiv_table['ich'].split(";")[0].split(" ")[0]

    """ Parsing imperative voice """

    imperative_table = get_conjugation_table(soup, "Imperative", "n/a")

    verb_conj['imperative_forms'] = []
    for word in imperative_table['du'].split(';'):
        word = word.strip().split(' ')[0]
        verb_conj['imperative_forms'].append(word)

    return verb_conj

def get_conjugation_table(soup, voice, tense):
    if voice == "Imperative":
        table = soup.find("h3", text=voice) \
                .parent \
                .find("table")
    else:
        table = soup.find("h3", text=voice) \
                .parent \
                .find("h4", text=tense) \
                .find_next_sibling("table")

    conjugation_table = {}

    for row in table.find_all('tr'):
        entries = list(row.children)
        pronoun = entries[0].text
        conjugated_verb = entries[1].text
        conjugation_table[pronoun] = conjugated_verb

    return conjugation_table
