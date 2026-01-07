# -*- coding: utf-8 -*-
{
    'name': 'Concrete Dispatching Dashboard',
    'version': '17.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Dashboard for Concrete Dispatching Management',
    'description': """
        Concrete Dispatching Dashboard
        ==============================
        This module provides a comprehensive dashboard for managing concrete dispatching operations:
        - Ticket Management
        - Load and Vehicle Assignment
        - Order Status Tracking
        - Real-time dispatching overview
    """,
    'author': 'XBoss',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'sale',
        'mrp',
        'fleet',
        'max_betong_sale',
        'max_betong_product',
        'max_betong_fleet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/dashboard_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            ('include', 'web._assets_helpers'),
            ('include', 'web._assets_primary_variables'),
            
            # CSS
            'max_betong_dashboard/static/src/css/dashboard.css',
            
            # Components - Search Input
            'max_betong_dashboard/static/src/components/search_input/index.js',
            'max_betong_dashboard/static/src/components/search_input/index.xml',
            
            # Components - Pagination
            'max_betong_dashboard/static/src/components/pagination/index.js',
            'max_betong_dashboard/static/src/components/pagination/index.xml',
            
            # Components - Confirm Modal
            'max_betong_dashboard/static/src/components/confirm_modal/index.js',
            'max_betong_dashboard/static/src/components/confirm_modal/index.xml',
            
            # Components - Column Menu
            'max_betong_dashboard/static/src/components/column_menu/index.js',
            'max_betong_dashboard/static/src/components/column_menu/index.xml',
            
            # Components - Station Dropdown
            'max_betong_dashboard/static/src/components/station_dropdown/index.js',
            'max_betong_dashboard/static/src/components/station_dropdown/index.xml',
            
            # Components - Context Menu
            'max_betong_dashboard/static/src/components/context_menu/index.js',
            'max_betong_dashboard/static/src/components/context_menu/index.xml',
            
            # Components - Status Badge
            'max_betong_dashboard/static/src/components/status_badge/index.js',
            'max_betong_dashboard/static/src/components/status_badge/index.xml',
            
            # Components - Progress Dots
            'max_betong_dashboard/static/src/components/progress_dots/index.js',
            'max_betong_dashboard/static/src/components/progress_dots/index.xml',
            
            # Components - Loading Overlay
            'max_betong_dashboard/static/src/components/loading_overlay/index.js',
            'max_betong_dashboard/static/src/components/loading_overlay/index.xml',
            
            # Components - Data Table
            'max_betong_dashboard/static/src/components/data_table/index.js',
            'max_betong_dashboard/static/src/components/data_table/index.xml',
            
            # Main Dashboard
            'max_betong_dashboard/static/src/js/dashboard.js',
            'max_betong_dashboard/static/src/xml/dashboard_templates.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
