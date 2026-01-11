from odoo import models, fields, api

class BlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    def _prepare_so_vals(
        self,
        customer,
        user_id,
        currency_id,
        pricelist_id,
        payment_term_id,
        client_order_ref,
        tag_ids,
        order_lines_by_customer,
    ):
        res = super()._prepare_so_vals(
            customer,
            user_id,
            currency_id,
            pricelist_id,
            payment_term_id,
            client_order_ref,
            tag_ids,
            order_lines_by_customer,
        )
        res['so_type'] = self.blanket_order_id.so_type
        return res

    def create_sale_order(self):
        res = super().create_sale_order()
        res['context'] = {'default_so_type': self.blanket_order_id.so_type}
        return res