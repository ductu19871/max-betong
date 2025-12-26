{
    'name': 'XBoss Report',
    'author': "XBoss",
    'website': 'https://git.e300.vn/xboss/core-report',
    'category': 'Base',
    'version': '17.0.0.0.6',
    'depends': [
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rule_data.xml',
        'views/report_paperformat_views.xml',
        'views/ir_actions_report_view.xml',
        'views/mail_template_views.xml',
        'views/report_template_config.xml',
        'views/report_template_parameter.xml',
        'views/menu_views.xml'
    ],
    'external_dependencies': {
        'bin': ['libreoffice'],
        'python': ['docx-mailmerge']
    },
    'auto_install': True,
    'license': 'LGPL-3'
}
