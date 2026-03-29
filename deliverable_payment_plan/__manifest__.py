{
    "name": "S-Curve Management",
    "version": "1.0",
    
    "depends": ["base", "sale", "purchase", "project", "account", "purchase_subcontractor_contract_odoo", "sale_customer_contract_odoo"],
    "data": [
        "views/res_company_view.xml",
        "views/payment_plan_views.xml",
        "security/ir.model.access.csv"
    ],
    "installable": True
}