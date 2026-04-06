{
    'name': 'Báo Cáo Sản Lượng Dashboard',
    'version': '17.0.1.0.0',
    'author': 'Xboss',
    'category': 'Sales/Sales',
    'summary': "Kế hoach sản lượng - thực tế",
    'description': "Dashboard Báo cáo sản lượng kế hoạch và thực tế",
    'depends': ['base', 'web', 'sale', 'project', 'deliverable_payment_plan'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'max_betong_output_dashboard/static/src/css/dashboard.css',
            'max_betong_output_dashboard/static/src/components/dashboard/dashboard.js',
            'max_betong_output_dashboard/static/src/components/dashboard/dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
}
