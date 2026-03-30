{
    'name': 'Max Bê Tông - Security',
    'version': '1.0',
    'category': 'Hidden',
    'summary': 'Phân quyền hệ thống ERP Bê Tông theo chức năng',
    'author': 'AHT',
    'depends': [
        'base',
        'sale_management',
        'purchase',
        'stock',
        'fleet',
        'mrp',
        'max_betong_dashboard',
        'xb_mrp_betong',
        'max_betong_sale',
        'max_betong_fleet',
        'max_betong_product',
        'model_access_deny',
        'ipc_interim_payment_certificates_odoo'
    ],
    'data': [
        # 'security/mrp/tech_res_groups.xml',
        'security/remove_inherits.xml',
        'security/mrp/res_groups.xml',
        'security/fleet/res_groups.xml',
        'security/purchase/res_groups.xml',
        'security/inventory/res_groups.xml',
        'security/mrp_origin/res_groups.xml',
        'security/betong_groups.xml',

        'security/mrp/ir.model.access.csv',
        'security/mrp/ir_model_denied.xml',
        'security/mrp/ir_rules.xml',

        'security/fleet/ir.model.access.csv',
        'security/fleet/ir_rule.xml',

        'security/inventory/ir.model.access.csv',
        'security/inventory/ir_model_denied.xml',

        'security/purchase/ir.model.access.csv',
        'security/purchase/ir_model_denied.xml',

        'security/mrp_origin/ir.model.access.csv',
        #menu
        'security/mrp/menu_mrp.xml',
        'security/inventory/menu_inventory.xml',
        'security/purchase/menu_purchase.xml',
        'security/fleet/menu_fleet.xml',
        'security/mrp_origin/menu_mrp_origin.xml',
        'views/pq_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
