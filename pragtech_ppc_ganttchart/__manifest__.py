# -*- coding: utf-8 -*-
{
    'name': "Project Planning and Gantt Chart",
    'version': '14.4',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': "www.pragtech.co.in",
    'category': 'Construction',
    'summary': """Created Gantt chart based on hierarchy of project,subproject,wbs,task groups and tasks""",
    'description': """
Project Planning and Gantt Chart
================================
Created Gantt chart based on hierarchy of project,subproject,wbs,task groups and tasks
<keywords>
gantt chart
project planning
construction gantt chart
project controlling
project planning in odoo
gantt chart in odoo 
construction
odoo construction
    """,
    'depends': ['web', 'base', 'pragtech_ppc','project'],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
#         'views/project_view.xml',
        'wizard/wizard_gantt_view.xml',

    ],
  'assets': {
        # 'web._assets_primary_variables': [
        #     'account/static/src/scss/variables.scss',
        # ],
        'web.assets_backend': [
            'pragtech_ppc_ganttchart/static/src/js/widgets.js',

        ],
       'web.assets_frontend': [
            'pragtech_ppc_ganttchart/static/src/js/initialization_copy.js',

        ],
        'web.assets_qweb': [
            'pragtech_ppc_ganttchart/static/src/xml/base.xml',
        ],
        # 'web.assets_frontend': [
        #     'pragtech_tender_management/static/src/js/tenders.js',

      # ],
},
    'qweb': ['static/src/xml/base.xml'],
    'demo': ['demo/demo.xml', ],
    'images': ['images/Animated-Construction-gantchart.gif'],
    'live_test_url': 'https://www.pragtech.co.in/company/proposal-form.html?id=103&name=Odoo-Construction-Management',
    'license': 'OPL-1',
    'price': 199,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
