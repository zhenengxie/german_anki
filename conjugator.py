""" Uses scraped data to conjugate and declenate German verbs, nouns 
and adjectives """

import dataset

DB = dataset.connect('sqlite:///.german.db')
VERBS = DB.get_table('verb')
NOUNS = DB.get_table('noun')
ADJVS = DB.get_table('adjective')

def conjugate_verb(inf):
    """ verb conjugater """
    data = VERBS.find_one(word=inf)

    if not data:
        print("oh no, not found")
        return {}

    conjugations = {'infinitive': inf}

    voices = [
        'first person singular',
        'second person singular informal',
        'third person singular',
        'second person plural',
        'first person plural',
        'second person singular formal'
        ]
    if data['seperable_prefix'] == '':
        seperable_end = ''
    else:
        seperable_end = ' ' + data['seperable_prefix']

    conjugations['present first person singular'] = data['present_stem'] + 'e' + seperable_end
    if data['e_on_present_second_third']:
        e_maybe = 'e'
    else:
        e_maybe = ''
    conjugations['present second person informal'] = data['present_second_third_stem'] + e_maybe + 'st' + seperable_end
    conjugations['present third person'] = data['present_second_third_stem'] + e_maybe + 't' + seperable_end
    conjugations['present second person'] = data['present_stem'] + e_maybe + 'st' + seperable_end
    conjugations['past participle'] = data['past_participle']

    return conjugations

def declenations_noun(noun):
    data = NOUNS.find_one(word=noun)
    decl = {}

    if data is None:
        return {}

    if data['type'] == 'de-decl-noun-m':
        gender = 'm'
    if data['type'] == 'de-decl-noun-f':
        gender = 'f'
    if data['type'] == 'de-decl-noun-n':
        gender = 'n'
    if data['type'] == 'de-decl-noun-pl':
        gender = 'pl'

    decl['Gender'] = gender

    if gender == 'pl':
        decl['Nominative Plural'] = noun
    if gender == 'm':
        decl['Nominative Singular'] = noun
    if gender == 'f':
        decl['Nominative Singular'] = noun
    if gender == 'n':
        decl['Nominative Singular'] = noun

    if gender == 'm' or gender == 'n':
        ending = data['genitive_singular_ending']

        if ending == '(e)s':
            decl['Genitive Singular Forms'] = [noun + 'es', noun + 's']
        else:
            decl['Genitive Singular Forms'] = [noun + ending]

    if gender == 'f':
        decl['Genitive Singular Forms'] = [noun]

    if gender in ['m', 'f', 'n']:
        if data['plural'] is not None:
            if data['plural'] != '-':
                decl['Nominative Plural'] = data['plural']
        elif data['plural_ending'] is not None:
            decl['Nominative Plural'] = noun + data['plural_ending']

    return decl

def declenations_adj(adj):
    data = ADJVS.find_one(word=adj)

    if data is None:
        return {}

    decl = {'lemma': adj}
    if data['stem']:
        stem = data['stem']
        if stem != adj:
            decl['stem'] = stem
    if data['pred']:
        pred = data['pred']
        if pred != adj:
            decl['pred'] = pred
    if data['comparative']:
        decl['comparative'] = data['comparative']
    if data['superlative']:
        decl['superlative'] = data['superlative']

    return decl
