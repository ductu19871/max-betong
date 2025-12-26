import base64
from odoo import fields, models, api, _
from odoo.addons.xb_report.models.report_template_config import OUT_TYPES


class MailTemplate(models.Model):
    _inherit = "mail.template"

    mailmerge_template_id = fields.Many2one('report.template.config', string="Mailmerge Template")
    mailmerge_output_type = fields.Selection(OUT_TYPES, string="Mailmerge  Output Type")
    
    def _generate_template_attachments(self, res_ids, render_fields, render_results=None):
        template_values = super(MailTemplate, self)._generate_template_attachments(res_ids,
                                                                                   render_fields,
                                                                                   render_results)
        if not self.mailmerge_template_id:
            return template_values

        source = self.env[self.model].browse(res_ids)
        if self.mailmerge_output_type:
            source = source.with_context(output_type=self.mailmerge_output_type) 
        stream, filename, output_type = source.action_get_mail_merge_reports(self.mailmerge_template_id.id, self.mailmerge_template_id.name)

        if output_type == 'docx':
            filename += '.docx'
        elif output_type == 'odt':
            filename += '.odt'
        elif output_type == 'pdf':
            filename += '.pdf'
        
        attachment_value = (filename, base64.b64encode(stream))
        for k, v in template_values.items():
            if 'attachments' not in v:
                v['attachments'] = []
            v['attachments'].append(attachment_value)
        return template_values