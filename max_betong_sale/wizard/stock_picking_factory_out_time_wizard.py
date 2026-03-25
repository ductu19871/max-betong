from odoo import fields, models

class StockPickingFactoryOutTimeWizard(models.TransientModel):
    _name = 'stock.picking.factory.out.time.wizard'
    _description = 'Update Factory Out Time Wizard'

    picking_id = fields.Many2one('stock.picking', required=True, ondelete='cascade')
    factory_out_time = fields.Datetime(string='Factory out time', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.picking_id.write({
            'factory_out_time': self.factory_out_time,
            'factory_out_time_manual': True,
        })
        return {'type': 'ir.actions.act_window_close'}
