# -*- coding: utf-8 -*-
{
    'name': 'Concrete Analytics Dashboard',
    'version': '17.0.1.1.0',
    'category': 'Sales/Sales',
    'summary': 'Analytics Dashboard for Concrete Operations',
    'description': """
        Concrete Analytics Dashboard
        ============================
        This module provides analytics and charts for concrete operations:
        - Volume delivery statistics
        - Vehicle trip analysis
        - Return volume charts
        - On-time delivery metrics
        - Concrete lifetime tracking
        - Vehicle cycle time analysis
    """,
    'author': 'XBoss',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'max_betong_dashboard',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # CSS
            'max_betong_dashboard_analytic/static/src/css/analytic_dashboard.css',
            
            # Chart Components
            'max_betong_dashboard_analytic/static/src/components/trips_per_vehicle_chart/index.js',
            'max_betong_dashboard_analytic/static/src/components/trips_per_vehicle_chart/index.xml',
            'max_betong_dashboard_analytic/static/src/components/return_volume_chart/index.js',
            'max_betong_dashboard_analytic/static/src/components/return_volume_chart/index.xml',
            'max_betong_dashboard_analytic/static/src/components/on_time_delivery_chart/index.js',
            'max_betong_dashboard_analytic/static/src/components/on_time_delivery_chart/index.xml',
            'max_betong_dashboard_analytic/static/src/components/concrete_lifetime_chart/index.js',
            'max_betong_dashboard_analytic/static/src/components/concrete_lifetime_chart/index.xml',
            'max_betong_dashboard_analytic/static/src/components/vehicle_cycle_time_chart/index.js',
            'max_betong_dashboard_analytic/static/src/components/vehicle_cycle_time_chart/index.xml',
            
            # Main Dashboard
            'max_betong_dashboard_analytic/static/src/js/analytic_dashboard.js',
            'max_betong_dashboard_analytic/static/src/xml/analytic_templates.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}

