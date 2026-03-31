{
    "name": "S-Curve Management",
    "version": "1.0",
    
    "depends": ["base", "sale", "purchase", "project", "account","odoo_job_costing_management",
                 "purchase_subcontractor_contract_odoo", "sale_customer_contract_odoo", 'xb_job_deliverable',
                 "xb_account_ipc", 'max_betong_output_dashboard'],
    "data": [
        "views/res_company_view.xml",
        "views/payment_plan_views.xml",
        "security/ir.model.access.csv"
    ],
    "installable": True
}