from odoo import models, fields,api
from odoo.exceptions import ValidationError


class WizardChangeState(models.TransientModel):
    _name = 'wizard.change.state'
    _description = 'Wizard Change Ticket State'
    
    state = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('not_available', 'Not Available'),
            ('broken', 'Broken')
        ],
        string='State',
    )
    note = fields.Text(
        string='Note',
    )
    
    def action_confirm(self):
        active_id = self.env.context.get('active_id')
        record = self.env['fleet.vehicle'].browse(active_id)
        record.message_post(
                body=f"""Note: {self.note}""")
        record.state_concrete = self.state
        return
        
        
        