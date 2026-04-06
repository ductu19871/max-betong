{
    'name': 'Báo Cáo Sản Lượng Dashboard',
    'version': '17.0.1.0.0',
    'author': 'Xboss',
    'category': 'Sales/Sales',
    'summary': "Kế hoach sản lượng - thực tế",
    'description': "Dashboard Báo cáo sản lượng kế hoạch và thực tế",
    "depends": ["base", "sale", "purchase", "project", "account","odoo_job_costing_management",
                 "purchase_subcontractor_contract_odoo", "sale_customer_contract_odoo", 'xb_job_deliverable',
                 "xb_account_ipc"],
    'data': [
        "security/ir.model.access.csv",
        "views/res_company_view.xml",
        "views/payment_plan_views.xml",
        "views/dashboard_menu.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'deliverable_payment_plan/static/src/css/dashboard.css',
            'deliverable_payment_plan/static/src/components/dashboard/dashboard.js',
            'deliverable_payment_plan/static/src/components/dashboard/dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
}
