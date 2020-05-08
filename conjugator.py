""" Uses scraped data to conjugate and declenate German verbs, nouns 
and adjectives """

import dataset
from german_anki.verbix import scrape_verbix

DB = dataset.connect('sqlite:///.local/share/Anki2/addons21/german_anki/german.db')
VERBS = DB.get_table('verb')
NOUNS = DB.get_table('noun')
ADJVS = DB.get_table('adjective')

def conjugate_verb(verb):
    data = VERBS.find_one(word=verb)

    if data is None:
        return {}

    return scrape_verbix(verb)


def declenations_noun(noun):
    return NOUNS.find_one(word=noun)

def declenations_adj(adj):
    return ADJVS.find_one(word=adj)
