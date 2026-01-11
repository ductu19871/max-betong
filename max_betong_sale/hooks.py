# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def uninstall_hook(cr, registry):
    """
    Uninstall hook to remove domain from mrp.mrp_production_action
    when module is uninstalled
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    action = env.ref('mrp.mrp_production_action', raise_if_not_found=False)
    if action:
        action.write({'domain': []})
    action = env.ref('sale_blanket_order.act_open_blanket_order_view', raise_if_not_found=False)
    if action:
        action.write({'domain': [], 'context': {}})

    action = env.ref('sale.action_orders', raise_if_not_found=False)
    if action:
        action.write({'domain': [('state', 'not in', ('draft', 'sent', 'cancel'))], 'context': {'search_default_my_quotation': 1}})

    action = env.ref('sale.action_quotations', raise_if_not_found=False)
    if action:
        action.write({'domain': [], 'context': {'search_default_my_quotation': 1}})

    cr.commit()

