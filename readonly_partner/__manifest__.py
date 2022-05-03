# -*- coding: utf-8 -*-
# ############################################################################################################
#                                   This addon was created by Muriel Rémi                                    #
#                                        Creation date: 07 April 2022                                        #
# ############################################################################################################
{
    'name' : "Readonly Partner",
    'version' : '1.1',
    'summary': "Readonly Partner",
    'sequence': -22,
    'author' : "Muriel Rémi Cyr",
    "license" : "LGPL-3",
    'description': """
        Readonly Partner
        ================
        This module disables creation and edition of res.partner
    """,
    'category': '',
    'images' : [],
    'depends' : ['base', 'account'],
    'data': [
        "views/partner.xml",
        "views/account.xml",
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
