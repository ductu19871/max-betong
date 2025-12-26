{
    'name': 'Office Template Report',
    'description': 'Is Easy an elegant and scalable solution to design reports using LibreOffice or OpenOffice.',
    'summary': 'Export data all objects odoo to OpenOffice, LibreOffice output files odt, pdf, doc, docx, ods',
    'category': 'All',
    'version': '17.0.0.0.7',
    'website': 'https://git.e300.vn/xboss/core-report',
    'license': 'AGPL-3',
    'author': 'xboss',
    'depends': [
        'web',
        'xb_report',
    ],
    'external_dependencies': {
        'python': ['py3o.template', 'genshi'],
    },
    'data': [
        'views/report_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'xb_report_office/static/src/js/report/action_manager_report.esm.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}