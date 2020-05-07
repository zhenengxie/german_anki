""" Example Web Scraper """

import os
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

OPTIONS = Options()
OPTIONS.headless = True
DRIVER = webdriver.Firefox(options=OPTIONS, executable_path="./geckodriver")

PATH = """file:///""" + os.path.abspath("template.html")
DRIVER.get(PATH)

def verb_conj(verb):
    """ Gets conjugated forms of a german verb """
    DRIVER.execute_script("""verbix.conjugate("{0}");""".format(verb))
    time.sleep(0.3)

    soup = BeautifulSoup(DRIVER.page_source, 'lxml')

    verb_conjugations = {}

    present_table = get_conjugation_table(soup, "present")
    verb_conjugations['ich'] = present_table['ich']
    verb_conjugations['du'] = present_table['ich']
    verb_conjugations['es'] = present_table['er;sie;es']
    verb_conjugations['ihr'] = present_table['ihr']
    verb_conjugations['wir'] = present_table['wir']

    verb_conjugations['aux'] = get_conjugation_table(soup, "perfect")['wir']

    verb_conjugations['imperfect'] = get_conjugation_table(soup, "imperfect")['ich']
    verb_conjugations['konjunctiv'] = get_conjugation_table(soup, "konjunctiv")['ich']
    verb_conjugations['imperative'] = get_conjugation_table(soup, "imperative")['du']

    print(verb_conjugations)

def get_conjugation_table(soup, tense):
    conjugation_table = {}

    table = soup.find(id=tense)
    for row in table.find_all('tr'):
        entries = list(row.children)
        pronoun = entries[0].text
        conjugated_verb = entries[1].text
        conjugation_table[pronoun] = conjugated_verb

    print(conjugation_table)
    return conjugation_table

verb_conj("segeln")

time.sleep(2)

verb_conj("umziehen")
