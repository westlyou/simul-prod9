# -*- coding: utf-8 -*-
# ############################################################################################################
#                                   This addon was created by Muriel Rémi                                    #
#                                        Creation date: 21 Mars 2022                                         #
# ############################################################################################################
{
    'name' : "Invoice Origin Type",
    'version' : '1.1',
    'summary': "Invoice Origin Type",
    'sequence': -21,
    'author' : "Muriel Rémi Cyr",
    "license" : "LGPL-3",
    'description': """
        Invoice Origin Type
        ===================
        This modules adds origin_type field in account.move to dinstingish either invoice is from to or amadeus
    """,
    'category': '',
    'website': '',
    'images' : [],
    'depends' : ['travel_agency'],
    'data': [
        "views/account.xml",
    ],
    'demo': [],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
