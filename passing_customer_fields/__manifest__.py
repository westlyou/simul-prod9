# ############################################################################################################
#                                   This module was created by Muriel Rémi                                   #
#                                         Creation date: 22 March 2022                                       #
# ############################################################################################################
# -*- coding: utf-8 -*-
{
    'name' : 'Passing Customer Fields',
    'version' : '1.1',
    'summary': 'Passing Customer Fields',
    'sequence': -20,
    'author' : 'Muriel Rémi Cyr',
    "license" : "LGPL-3",
    'description': """
        Passing Customer Fields
        =======================
        This module adds new fields for passing customers in account move
    """,
    'category': '',
    'website': 'https://www.odoo.com/page/billing',
    'images' : [],
    'depends' : ['base', 'account'],
    'data': [
        "views/account.xml"
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
