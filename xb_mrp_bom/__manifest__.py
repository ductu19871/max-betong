{
    "name": "MRP BoM custom by Xboss",
    "summary": "MRP BoM custom by Xboss",
    "version": "17.0.1.0.1",
    "license": "AGPL-3",
    "author": "Xboss",
    "depends": [
        "max_betong_sale",
        "mrp_bom_version",
        "max_betong_product",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/mrp_bom_view.xml',
        'wizard/mrp_bom_create_new_version_wizard_views.xml',
    ],
    "installable": True,
}
