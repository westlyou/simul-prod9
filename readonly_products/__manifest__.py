# -*- coding: utf-8 -*-
# ############################################################################################################
#                                   This addon was created by Muriel Rémi                                    #
#                                        Creation date: 13 April 2022                                        #
# ############################################################################################################
{
    'name' : "Readonly Products",
    'version' : '1.1',
    'summary': "Readonly Products",
    'sequence': -22,
    'author' : "Muriel Rémi Cyr",
    "license" : "LGPL-3",
    'description': """
        Readonly Products
        =================
        This module disables creation and edition of products
    """,
    'category': '',
    'images' : [],
    'depends' : ['base', 'account'],
    'data': [
        "views/account.xml",
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
