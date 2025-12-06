# -*- coding: utf-8 -*-
{
    'name': 'Max Betong Product',
    'version': '17.0.1.0.0',
    'category': 'Product',
    'summary': 'Quản lý sản phẩm bê tông với thời gian sống',
    'description': """
        Module quản lý sản phẩm bê tông:
        - Phân loại sản phẩm bê tông
        - Quản lý thời gian sống của bê tông (tính bằng phút)
        - Hỗ trợ kiểm soát chất lượng và điều phối giao hàng
    """,
    'author': 'Maxsolution',
    'depends': ['product', 'sale'],
    'data': [
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

