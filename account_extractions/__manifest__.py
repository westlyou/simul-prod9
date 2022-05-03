# -*- coding: utf-8 -*-
# ############################################################################################################
#                                   This addon was created by Muriel Rémi                                    #
#                                        Creation date: 19 Mars 2022                                         #
# ############################################################################################################
{
    'name' : "Account Extractions",
    'version' : '1.1',
    'summary': "Account Extractions",
    'sequence': -21,
    'author' : "Muriel Rémi Cyr",
    "license" : "LGPL-3",
    'description': """
        Account Extractions
        ===================
        This modules allows to extract account data like sales log and state per company
    """,
    'category': '',
    'website': '',
    'images' : [],
    'depends' : ['travel_agency'],
    'data': [
        "security/ir.model.access.csv",
        "views/account_extractions.xml",
        "reports/report.xml",
        "reports/report_template.xml"
    ],
    'demo': [],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
