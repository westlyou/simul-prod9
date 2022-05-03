# -*- coding: utf-8 -*-
# ############################################################################################################
#                                   This addon was created by Muriel Rémi                                    #
#                                      Creation date: 21 February 2022                                       #
# ############################################################################################################
{
    'name' : "Hide Draft Invoice Button",
    'version' : '1.1',
    'summary': "Hide Draft Invoice Button",
    'sequence': -20,
    'author' : "Muriel Rémi Cyr",
    "license" : "LGPL-3",
    'description': """
        Hide Draft Invoice Button
        =========================
        This module hide draft invoice button
    """,
    'category': '',
    'website': 'https://www.odoo.com/page/billing',
    'images' : [],
    'depends' : ['account'],
    'data': [
        'views/account.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
