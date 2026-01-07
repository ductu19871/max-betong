# -*- coding: utf-8 -*-
{
    'name': 'Max Betong Fleet',
    'version': '17.0.1.0.0',
    'category': 'fleet',
    'description': """""",
    'author': 'Maxsolution',
    'depends': ['fleet','mrp'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_change_state.xml',
        'views/fleet_vehicle_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'max_betong_fleet/static/src/css/selection_state_badge.css',
            'max_betong_fleet/static/src/js/selection_state_badge.js',
            'max_betong_fleet/static/src/xml/selection_state_badge.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

