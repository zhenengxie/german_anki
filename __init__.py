""" Anki autofiller """

from anki.hooks import addHook
import hashlib
from google.cloud import texttospeech
from german_anki.conjugator import conjugate_verb, declenations_noun, declenations_adj
from bs4 import BeautifulSoup
from aqt import mw
from aqt.editor import Editor


CLIENT = texttospeech.TextToSpeechClient()
VOICE = texttospeech.types.VoiceSelectionParams(
        language_code='de-DE',
        name='de-DE-Wavenet-B')
AUDIO_CONFIG = texttospeech.types.AudioConfig(
    audio_encoding=texttospeech.enums.AudioEncoding.MP3)

def tts(text, prefix = None):
    text = BeautifulSoup(text, "lxml").text # parsing out all html tags
    if prefix is not None:
        text = prefix + ' ' + text
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

def add_sound_to_field(note, field, prefix=None):
    if note[field]:
        note[field + ' Sound'] = tts(note[field], prefix = prefix)

def add_sound(note, note_type):
    if note_type == 'noun':
        for field in ['Nominative Singular', 'Nominative Plural', 'Genitive Singular']:
            add_sound_to_field(note, field)
    if note_type == 'adj':
        for field in ['Lemma', 'Predicative', 'Comparative', 'Superlative']:
            add_sound_to_field(note, field)
    if note_type == 'verb':
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
            add_sound_to_field(note, field, prefix)
    if note_type == 'general':
        add_sound_to_field(note, 'German')

def format_noun(gender, word, case):
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

    if gender == 'pl':
        rawtext = word
    else:
        rawtext = articles[(gender, case)] + ' ' + word

    return """<span class="{0}">{1}</span>""".format(gender, rawtext)

def comma_join(lst):
    return ", ".join(lst)


GERMAN_NOUN_NAME = "German Nouns"
GERMAN_ADJV_NAME = "German Adjectives"
GERMAN_VERB_NAME = "German Verbs"
GERMAN_GENR_NAME = "German General"

def onFocusLost(flag, note, fidx):
    note_type = note.model()['name']
    field_indices = {card: i for i, card in enumerate(mw.col.models.fieldNames(note.model()))}
    
    if note_type == GERMAN_NOUN_NAME:
        if field_indices['Auto'] == fidx and not note['Manual Override']:
            nouns = [noun.strip() for noun in note['Auto'].strip().split(',')]
            decls = [declenations_noun(noun) for noun in nouns]
            decls = [decl for decl in decls if decl]

            nom_sing = []
            for decl in decls:
                if 'Nominative Singular' in decl:
                    nom_sing.append(format_noun(decl['Gender'], decl['Nominative Singular'], 'nom'))
            nom_sing = ", ".join(nom_sing)
            note['Nominative Singular'] = nom_sing

            nom_pl = []
            nom_pl_raw = []
            for decl in decls:
                if 'Nominative Plural' in decl:
                    nom_pl.append(format_noun('pl', decl['Nominative Plural'], 'nom'))
            nom_pl = ", ".join(nom_pl)
            note['Nominative Plural'] = nom_pl

            if any(decl['Gender'] in ['m', 'n'] for decl in decls):
                gen_forms = []
                for decl in decls:
                    if 'Genitive Singular Forms' in decl:
                        gen_forms += [format_noun(decl['Gender'], form, 'gen')
                                for form in decl['Genitive Singular Forms']]
                note['Genitive Singular'] = ", ".join(gen_forms)
            else:
                note['Genitive Singular'] = ""

        if field_indices['Manual Override'] == fidx and note['Manual Override'] == 'i':
            if note['Nominative Singular']:
                words_nom_sing = note['Nominative Singular'].split(', ')
                words_nom_sing_formatted = []
                for word in words_nom_sing:
                    word = word.strip()
                    gender = word.split(' ')[0]
                    word = word[len(gender) + 1:]
                    words_nom_sing_formatted.append(format_noun(gender, word, 'nom'))
                note['Nominative Singular'] = ", ".join(words_nom_sing_formatted)

            if note['Genitive Singular']:
                words_nom_sing = note['Genitive Singular'].split(', ')
                words_nom_sing_formatted = []
                for word in words_nom_sing:
                    word = word.strip()
                    gender = word.split(' ')[0]
                    word = word[len(gender) + 1:]
                    words_nom_sing_formatted.append(format_noun(gender, word, 'gen'))
                note['Genitive Singular'] = ", ".join(words_nom_sing_formatted)

            if note['Nominative Plural']:
                words_pl = note['Nominative Plura'].split(', ')
                words_pl_formatted = []
                for word in words_pl:
                    words_pl_formatted.append(format_noun('pl', word, 'nom'))
                note['Nominative Plural'] = ", ".join(words_pl_formatted)

            note['Manual Override'] = 'a'

    if note_type == GERMAN_ADJV_NAME:
        if field_indices['Auto'] == fidx and not note['Manual Override']:
            adjs = [adj.strip() for adj in note['Auto'].split(',')]
            decls = [declenations_adj(adj) for adj in adjs]
            decls = [decl for decl in decls if decl]

            lemmas = [decl['lemma'] for decl in decls if 'lemma' in decl]
            stems = [decl['stem'] for decl in decls if 'stem' in decl]
            preds = [decl['pred'] for decl in decls if 'pred' in decl]
            comps = [decl['comparative'] for decl in decls if 'comparative' in decl]
            sups = ['am ' + decl['superlative'] + 'en' for decl in decls if 'superlative' in decl]

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


    if note_type == GERMAN_VERB_NAME:
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
                    note['Aux Past Participle'] = "haben {0}, sein {0}".format(conj['Past Participle'])

                note['Imperative Singular'] = ', '.join(conj['Imperative Singular'])

    if any(field in field_indices and field_indices[field] == fidx for field in ['Auto', 'German', 'Manual Override']):
        if 'Manual Override' in note and (not note['Manual Override'] or note['Manual Override'] == 'a'):
            if note_type == GERMAN_NOUN_NAME:
                add_sound(note, 'noun')
            if note_type == GERMAN_VERB_NAME:
                add_sound(note, 'verb')
            if note_type == GERMAN_ADJV_NAME:
                add_sound(note, 'adj')
            if note_type == GERMAN_GENR_NAME or note_type == 'German Phrases':
                add_sound(note, 'general')
            return True

    return flag

addHook("editFocusLost", onFocusLost)

def clearFields(self):
    for field in mw.col.models.fieldNames(self.note.model()):
        self.note[field] = ''
    self.note.flush()
    mw.reset()

def noteStyle(self):
    self.web.eval("""wrap('<span class="inlinenote">', '</span>');""")


def onSetupShortcuts(cuts, self):
    cuts += [("Ctrl+Y", self.clearFields),
             ("Ctrl+Shift+W", self.noteStyle)]
    
Editor.noteStyle = noteStyle
Editor.clearFields = clearFields
addHook("setupEditorShortcuts", onSetupShortcuts)
