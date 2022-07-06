# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Contract Amendment",
    'summary': "HR Contract Amendment",
    'description': """ Transfer Employee""",
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'http://www.synconics.com',
    'category': 'HR',
    'version': '14.0.1.0',
    'license': 'OPL-1',
    'depends': ['hr_payroll', 'hr_warning'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/cron.xml',
        'data/mail_template.xml',
        'views/transfer_employee_view.xml',
    ],
    'demo': [
        'demo/demo.xml'
    ],
    'installable': True,
    'auto_install': False,
}
