# -*- coding: utf-8 -*-
{
    'name': 'Max Betong Sale',
    'version': '17.0.1.0.0',
    'category': 'Sale',
    'summary': 'Sale',
    'description': """
    """,
    'author': 'Maxsolution',
    'depends': ['max_betong_product','sale_management',
                'sale_mrp','max_betong_fleet','base_geolocalize'],
    'data': [
        #data
        #wizard
        "wizard/wizard_confirm_fields.xml",
        #view
        'views/sale_order_views.xml',
        'views/betong_load_views.xml',
        'views/mrp_bom_view.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        #menu
        'views/menu_views.xml',
        #security
        'security/security.xml',
        'security/ir.model.access.csv',
        
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

