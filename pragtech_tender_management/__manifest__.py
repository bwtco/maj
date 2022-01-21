{
    'name': 'Odoo Tender Management',
    'version': '15.0.2',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': "www.pragtech.co.in",
    'category': 'Construction',
    'depends': ['resource', 'product', 'website', 'website_sale'],
    'description': """
Odoo Tender Management System
=============================
This app has below features:
----------------------------
    1) Tender publication
    2) Pre-bid meeting and MOM
    3) Final tender correction and publication 
    4) Technical bids submission
    5) Financial bids submission
    6) Bids comparison and bid winner announcement
<keywords>
odoo tender management
tender management
tender management app
tender management software
tender
odoo tender
    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/tenders_view.xml',
        'views/bids_view.xml',
        'views/assets.xml',
        'data/entry.xml',
        'views/tenders_template.xml',
        'views/rank_template.xml',
        'views/tenders_labours.xml',
        'views/bids_template.xml',
        'views/logged_in_template.xml',
    ],
    'assets': {
        # 'web._assets_primary_variables': [
        #     'account/static/src/scss/variables.scss',
        # ],
        # 'web.assets_backend': [
        #     # 'account/static/src/js/account_selection.js',
        # ],
        'web.assets_frontend': [
            'pragtech_tender_management/static/src/js/tenders.js',

      ],
},
    'images': ['images/Animated-tender-management.gif'],
    'license': 'OPL-1',
    'price': 149,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
