{
    'name': 'XB Fleet Extension',
    'version': '17.0.1.0.1',
    'summary': 'Mở rộng đội xe: trường bổ sung, nhóm quyền',
    'author': 'Your Company',
    'category': 'Fleet',
    'depends': ['fleet', 'analytic'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/analytic_plan_data.xml',
        'views/fleet_vehicle_views.xml',
        'views/fleet_menus.xml',
    ],
    'demo': [
        'demo/demo_vehicles.xml',
        'demo/demo_projects.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
} 