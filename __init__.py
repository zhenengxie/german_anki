""" Anki autofiller """

from anki.hooks import addHook
import hashlib
from google.cloud import texttospeech
from german_anki.conjugator import conjugate_verb, declenations_noun, declenations_adj

CLIENT = texttospeech.TextToSpeechClient()
VOICE = texttospeech.types.VoiceSelectionParams(
        language_code='de-DE',
        name='de-DE-Wavenet-B')
AUDIO_CONFIG = texttospeech.types.AudioConfig(
    audio_encoding=texttospeech.enums.AudioEncoding.MP3)

def tts(text):
    filename = "german-gtts-{0}.mp3".format(hashlib.md5(text.encode('utf-8')).hexdigest())

    try:
        out = open(filename, 'r')
        out.close()
    except FileNotFoundError: # only generate speech if the text is new
        synthesis_input = texttospeech.types.SynthesisInput(text=text)
        response = CLIENT.synthesize_speech(synthesis_input, VOICE, AUDIO_CONFIG)
        with open(filename, 'wb') as out:
            out.write(response.audio_content)

    return "[sound:{0}]".format(filename)

def format_noun(gender, word, case, raw):
    articles = {
            ('m', 'nom'): 'der',
            ('f', 'nom'): 'die',
            ('n', 'nom'): 'das',
            ('pl', 'nom'): 'die',
            ('m', 'gen'): 'des',
            ('f', 'gen'): 'der',
            ('n', 'gen'): 'des',
            ('pl', 'gen'): 'der'
            }

    rawtext = articles[(gender, case)] + ' ' + word
    if raw:
        return rawtext
    else:
        return """<span class="{0}">{1}</span>""".format(gender, rawtext)

def comma_join(lst):
    return ", ".join(lst)

def onFocusLost(flag, note, fidx):
    from aqt import mw
    
    if note.model()['name'] == 'AUTO German Nouns':
        field_indices = {card: i for i, card in enumerate(mw.col.models.fieldNames(note.model()))}
        if field_indices['Auto'] == fidx and not note['Manual Override']:
            nouns = [noun.strip() for noun in note['Auto'].strip().split(',')]
            decls = [declenations_noun(noun) for noun in nouns]
            decls = [decl for decl in decls if decl]

            nom_sing = []
            nom_sing_raw = []
            for decl in decls:
                if 'Nominative Singular' in decl:
                    nom_sing.append(format_noun(decl['Gender'],
                        decl['Nominative Singular'], 'nom', False))
                    nom_sing_raw.append(format_noun(decl['Gender'],
                        decl['Nominative Singular'], 'nom', True))
            nom_sing = ", ".join(nom_sing)
            nom_sing_raw = ", ".join(nom_sing_raw)
            note['Nominative Singular'] = nom_sing
            if nom_sing_raw:
                note['Nominative Singular Sound'] = tts(nom_sing_raw)

            nom_pl = []
            nom_pl_raw = []
            for decl in decls:
                if 'Nominative Plural' in decl:
                    nom_pl.append(format_noun('pl',
                        decl['Nominative Plural'], 'nom', False))
                    nom_pl_raw.append(format_noun('pl',
                        decl['Nominative Plural'], 'nom', True))
            nom_pl = ", ".join(nom_pl)
            nom_pl_raw = ", ".join(nom_pl_raw)
            note['Nominative Plural'] = nom_pl
            if nom_pl_raw:
                note['Nominative Plural Sound'] = tts(nom_pl_raw)

            if any(decl['Gender'] in ['m', 'n'] for decl in decls):
                gen_forms = []
                gen_forms_raw = []
                for decl in decls:
                    if 'Genitive Singular Forms' in decl:
                        gen_forms += [format_noun(decl['Gender'], form, 'gen', False)
                                for form in decl['Genitive Singular Forms']]
                        gen_forms_raw += [format_noun(decl['Gender'], form, 'gen', True)
                                for form in decl['Genitive Singular Forms']]
                note['Genitive Singular'] = ", ".join(gen_forms)
                note['Genitive Singular Sound'] = tts(", ".join(gen_forms_raw))

            return True

    if note.model()['name'] == 'AUTO German Adjectives':
        field_indices = {card: i for i, card in enumerate(mw.col.models.fieldNames(note.model()))}
        if field_indices['Auto'] == fidx and not note['Manual Override']:
            adjs = [adj.strip() for adj in note['Auto'].split(',')]
            decls = [declenations_adj(adj) for adj in adjs]
            decls = [decl for decl in decls if decl]

            lemmas = [decl['lemma'] for decl in decls if 'lemma' in decl]
            stems = [decl['stem'] for decl in decls if 'stem' in decl]
            preds = [decl['pred'] for decl in decls if 'pred' in decl]
            comps = [decl['comparative'] for decl in decls if 'comparative' in decl]
            sups = [decl['superlative'] for decl in decls if 'superlative' in decl]

            lemmas = comma_join(lemmas)
            note['Lemma'] = lemmas
            note['Lemma Sound'] = tts(lemmas)

            for field, values in [
                    ('Stem', stems),
                    ('Predicative', preds),
                    ('Comparative', comps),
                    ('Superlative', sups)
                    ]:
                if values:
                    values = comma_join(values)
                    note[field] = values
                    if field != 'Stem':
                        note[field + ' Sound'] = tts(values)
            return True

    if note.model()['name'] == 'AUTO German Verbs':
        field_indices = {card: i for i, card in enumerate(mw.col.models.fieldNames(note.model()))}
        if field_indices['Auto'] == fidx and not note['Manual Override']:
            inf = note['Auto'].strip()

            conj = conjugate_verb(inf)

            if conj:
                for field in [
                        'Present 1', 'Present 2 Sing', 'Present 3', 'Present 1 3 Plural 2 Formal',
                        'Present 2 Plural', 'Imperfect 1', 'Conjunctive II 1', 'Infinitive']:
                    note[field] = conj[field]

                if conj['aux'] == 'h':
                    note['Aux Past Participle'] = "haben {0}".format(conj['Past Participle'])
                if conj['aux'] == 's':
                    note['Aux Past Participle'] = "sein {0}".format(conj['Past Participle'])
                if conj['aux'] == 'hs':
                    note['Aux Past Participle'] = "habe {0}, sein {0}".format(conj['Past Participle'])

                note['Imperative Singular'] = ', '.join(conj['Imperative Singular'])

                for prefix, field in [
                        ('', 'Infinitive'),
                        ('ich ', 'Present 1'),
                        ('du ', 'Present 2 Sing'),
                        ('es ', 'Present 3'),
                        ('wir ', 'Present 1 3 Plural 2 Formal'),
                        ('ihr ', 'Present 2 Plural'),
                        ('', 'Aux Past Participle'),
                        ('', 'Imperative Singular'),
                        ('ich ', 'Conjunctive II 1'),
                        ('ich ', 'Imperfect 1')
                        ]:
                    note[field + ' Sound'] = tts(prefix + note[field])

            return True

    return False

addHook("editFocusLost", onFocusLost)
