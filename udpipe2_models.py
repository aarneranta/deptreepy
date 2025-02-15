
model_dict = {
    'Bul': 'bulgarian-btb-ud-2.12-230717',
    'Chi': 'chinese-gsdsimp-ud-2.15-241121',
    'Cze': 'czech-pdt-ud-2.12-230717',
    'Eng': 'english-ewt-ud-2.12-230717',
    'Fin': 'finnish-tdt-ud-2.12-230717',
    'Fre': 'french-gsd-ud-2.12-230717',
    'Ger': 'german-gsd-ud-2.12-230717',
    'Gre': 'greek-gud-ud-2.15-241121',
    'Hrv': 'croatian-set-ud-2.12-230717',
    'Ita': 'italian-isdt-ud-2.12-230717',
    'Por': 'portuguese-bosque-ud-2.12-230717',
    'Spa': 'spanish-gsd-ud-2.12-230717',
    'Swe': 'swedish-talbanken-ud-2.12-230717'
    }
## TODO: complete this from
# https://lindat.mff.cuni.cz/services/udpipe/api/models


default_model = model_dict['Eng']

def udpipe2_model(lang):
    return model_dict.get(lang, default_model)

