from odoo import models, fields,api
from odoo.exceptions import ValidationError


class WizardChangeState(models.TransientModel):
    _inherit = 'wizard.change.state'
    
    state_ticket = fields.Selection(
        selection=[
            ('loaded', 'Loaded'),
            ('leave', 'Leave'),
            ('arrived', 'Arrived'),
            ('unloading', 'Unloading'),
            ('return', 'Return'),
            ('completed', 'Completed'),
        ],
        string='State',
    )
    
    def action_confirm_ticket(self):
        active_id = self.env.context.get('active_id')
        record = self.env['mrp.production'].browse(active_id)
        if record.state_concrete in ('assigned','loading'):
            record.vehicle_id.state_concrete = self.state_ticket
            for workorder_id in record.workorder_ids:
                workorder_id.button_finish()
        if record.state_concrete in ('loaded','leave','arrived','unloading','return'):
            if record.state_concrete ==self.state_ticket:
                return
            record.vehicle_id.state_concrete = self.state_ticket
        record.message_post(
                body=f"""Note: {self.note}""")
        record.state_concrete = self.state_ticket
        return
        
        
        