# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Copy Center Process",
    'summary': """ HR Copy Center Process """,
    'description': """
        Copy center – if any employee wants to generate hard copies of any official document then here they will select
        type of papers & number of copies and then at last related employee expense will be generated.
        Expense will be paid by company & employee contribution will be directly deducted from employee's payslip.

        Basic Flow of this module like this:
        New -> Confirm(Employee) -> Approve(HR Officer) -> Inprogress(Admin Manager) -> Done(Admin Manager) -> Generate Expense(Admin Manager)
    """,
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'http://www.synconics.com',
    'category': 'HR',
    'version': '1.0',
    'license': 'OPL-1',
    'depends': ['product', 'hr_admin', 'hr_expense_payment'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/product_data.xml',
        'views/hr_copy_center_view.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/demo.xml'
    ],
    'images': [
        'static/description/main_screen.png'
    ],
    "price": 0.0,
    "currency": "EUR",
    'installable': True,
    'auto_install': False,
}
