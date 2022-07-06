# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Middle East Human Resource contract",
    'summary': """ Employee Contract """,
    'description': """ Enhance the feature of base hr_contract module according to Middle East Human Resource. """,
    'author': "Synconics Technologies Pvt. Ltd.",
    'website': "http://www.synconics.com",
    'category': 'HR',
    'version': '1.0',
    'sequence': 20,
    'license': 'OPL-1',
    'depends': ['account',
                'hr_contract',
                'saudi_hr',
                'hr_payroll_base',
                ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/hr_payroll_data.xml',
        'data/contract_cron.xml',
        'data/contract_template.xml',
        'views/contract_view.xml',
        'report/empcontract_report_qweb.xml',
        'report/newjoin_empcontract_reportqweb.xml',
        'views/register_qweb_report.xml',
    ],
    'demo': [
        'demo/demo.xml'
        ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
