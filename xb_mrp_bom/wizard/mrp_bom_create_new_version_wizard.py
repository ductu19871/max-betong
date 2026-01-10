from odoo import fields, models, api, _


class MrpBomCreateNewVersionWizard(models.TransientModel):
    _name = 'mrp.bom.create_new_version.wizard'
    _description = 'Create New Version'

    bom_id = fields.Many2one('mrp.bom', string='BoM', required=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', check_company=True)
    company_id = fields.Many2one('res.company', related='bom_id.company_id', string='Company', store=True)

    def get_context_default_values(self):
        return {
            'workcenter_id': self.workcenter_id.id,
        }

    def action_create_new_version(self):
        return self.bom_id.with_context(
            from_wizard_create_new_version=True,
            default_bom_vals=self.get_context_default_values()
        ).button_new_version()
