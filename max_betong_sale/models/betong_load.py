# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BetongLoad(models.Model):
    """
    Load model for Concrete SO
    This model stores Load information allocated from SO
    """
    _name = 'betong.load'
    _description = 'Concrete Load'

    name = fields.Char(string='Load Name', required=True)
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
        index=True
    )
    volume = fields.Float(
        string='Volume (m³)',
        required=True,
        help='Volume of this Load'
    )

    @api.model
    def create(self, vals):
        """Override to auto-update SO's volume_allocated"""
        load = super(BetongLoad, self).create(vals)
        if load.sale_order_id:
            # Trigger recompute
            load.sale_order_id._compute_volume_allocated()
        return load

    def write(self, vals):
        """Override to auto-update SO's volume_allocated"""
        result = super(BetongLoad, self).write(vals)
        if 'volume' in vals or 'sale_order_id' in vals:
            for load in self:
                if load.sale_order_id:
                    # Trigger recompute
                    load.sale_order_id._compute_volume_allocated()
        return result

    def unlink(self):
        """Override to auto-update SO's volume_allocated when deleting"""
        sale_orders = self.mapped('sale_order_id')
        result = super(BetongLoad, self).unlink()
        for order in sale_orders:
            if order:
                # Trigger recompute
                order._compute_volume_allocated()
        return result

