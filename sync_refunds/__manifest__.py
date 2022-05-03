# -*- coding: utf-8 -*-
# ############################################################################################################
#                                   This addon was created by Muriel Rémi                                    #
#                                        Creation date: 01 April 2022                                        #
# ############################################################################################################
{
    'name' : "Synchronize Refunds",
    'version' : '1.1',
    'summary': "Synchronize Refunds",
    'sequence': -21,
    'author' : "Muriel Rémi Cyr",
    "license" : "LGPL-3",
    'description': """
        Synchronize Refunds
        ===================
        This module synchronizes supplier refunds with customer refunds
    """,
    'category': '',
    'website': 'https://www.odoo.com/page/billing',
    'images' : [],
    'depends' : ['account'],
    'data': [
        "views/account.xml",
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
