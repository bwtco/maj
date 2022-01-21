# -*- coding: utf-8 -*-
{
    'name': "Contracting Debit/Credit/Advance/Retention Transactions",
    'version': '15.0',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': "www.pragtech.co.in",
    'category': 'Construction',
    'summary': """Contracting Transactions""",
    'description': """
        Contracting Transactions
        Odoo version - V12
    """,
    'depends': ['base', 'pragtech_contracting', 'pragtech_ppc'],
    'data': [
        'views/menus.xml',
        'views/ra_bill.xml',
    ],
    'images': ['images/Construction-transaction.png'],

    'license': 'OPL-1',
    'price': 99,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
