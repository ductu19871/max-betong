{
    'name': "MRP Production Dynamic State",
    'version': '17.0.0.0.1',
    'depends': [
        'mrp',
    ],
    'license': 'Other proprietary',
    'summary': """Dynamic State Management for Manufacturing Orders.""",
    'description':
"""
This module allows you to create custom dynamic states for manufacturing orders (mrp.production)
and map them to the original states. This provides flexibility in customizing the workflow
and status tracking for production orders.
""",
    'author': "Xboss",
    'website': "http://www.xboss.com",
    'data':[
        'security/ir.model.access.csv',
        'data/mrp_production_state_data.xml',
        'views/mrp_production_state_views.xml',
        'views/mrp_production_views.xml',
    ],
    'installable' : True,
    'application' : False,
    'auto_install' : False,
    'post_init_hook': 'post_init_hook',
}

