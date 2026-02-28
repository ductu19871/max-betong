# -*- coding: utf-8 -*-
{
    'name': 'Max Betong Sale',
    'version': '17.0.1.0.3',
    'category': 'Sale',
    'summary': 'Sale',
    'description': """
    """,
    'author': 'Maxsolution',
    'depends': ['max_betong_product','sale_management',
                'sale_mrp','max_betong_fleet','base_geolocalize', 'sale_blanket_order'],
    'data': [
        #data
        #wizard
        "wizard/wizard_confirm_fields.xml",
        "wizard/wizard_change_state.xml",
        #view
        'views/sale_order_views.xml',
        'views/betong_load_views.xml',
        'views/mrp_bom_view.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/mrp_production_views.xml',
        'views/stock_picking_view.xml',
        'views/product_views.xml',
        'views/sale_blanket_order_views.xml',
        'views/report_delivered_volume_views.xml',
        'views/report_on_time_delivery_views.xml',
        'views/report_rejected_volume_views.xml',
        'views/report_cycle_time_views.xml',
        'views/report_trip_per_truck_report.xml',
        'views/report_concrete_lifetime_report.xml',
        'wizard/change_production_qty_views.xml',
        #menu
        'views/menu_views.xml',
        #security
        'security/security.xml',
        'security/ir.model.access.csv',
        #report
        'report/template.xml',
        
    ],
    'assets': {
        'web.assets_backend': [
            'max_betong_sale/static/src/js/**/*',
            'max_betong_sale/static/src/scss/**/*'
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'uninstall_hook': 'uninstall_hook',
}

