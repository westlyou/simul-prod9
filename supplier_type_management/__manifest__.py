# -*- coding: utf-8 -*-
# ############################################################################################################
#                                   This addon was created by Muriel Rémi                                    #
#                                        Creation date: 16 March 2022                                        #
# ############################################################################################################
{
    'name' : "Supplier Type Management",
    'version' : '1.1',
    'summary': "Supplier Type Management",
    'sequence': -21,
    'author' : "Muriel Rémi Cyr",
    "license" : "LGPL-3",
    'description': """
        Supplier Type Management
        ========================
        This module is created to manage type of supplier
    """,
    'category': '',
    'website': 'https://www.odoo.com/page/billing',
    'images' : [],
    'depends' : ['base', 'account', 'contacts_from_incadea', 'supplier_from_incadea'],
    'data': [
        "views/partner.xml",
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
