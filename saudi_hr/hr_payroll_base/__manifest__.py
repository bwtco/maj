# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Payroll Base",
    'summary': "HR Payroll Base",
    'description': """
        """,
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'http://www.synconics.com',
    'category': 'Human Resources/Payroll',
    'version': '1.0',
    'license': 'OPL-1',
    'depends': ['hr_payroll_account'],
    'data': [
        'data/hr_payroll_data.xml',
    ],
    'demo': [],
    'images': [
        'static/description/main_screen.jpg'
    ],
    "price": 0.0,
    "currency": "EUR",
    'installable': True,
    'auto_install': False,
}
