'''This file has objects used for making maps of Texas. Objects here are
    intended for maps of Texas made with specific style guidelines'''

import pandas as pd

Texas_city_label_dict = {'city_names': ['El Paso', 'Odessa', 'Amarillo',
                                        'Lubbock', 'Fort Worth', 'Dallas',
                                        'Waco', 'Tyler', 'Brownsville',
                                        'San Antonio', 'Austin', 'Laredo',
                                        'Corpus Christi', 'College Station',
                                        'Houston', 'Galveston'],
                         'city_positions': ['bot_left', 'top_right', 'top_left',
                                            'top_left', 'bot_left', 'top_right',
                                            'top_left', 'top_left', 'bot_left',
                                            'top_left', 'top_left', 'bot_left',
                                            'bot_right', 'top_left',
                                            'top_left', 'bot_right'],
                         'dx': [.005, .005, .005,
                                .005, .005, .005,
                                .005, .005, .005,
                                .005, .005, .0065,
                                .024, .005,
                                .005, .005],
                         'dy': [.005, .005, .005,
                                .005, .005, .005,
                                .005, .005, .005,
                                .005, .005, .004,
                                .005, .005,
                                .005, .005]}


Texas_city_label_df = pd.DataFrame.from_dict(Texas_city_label_dict)
