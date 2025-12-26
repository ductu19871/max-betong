import re
from odoo import models, fields, api, _

OUT_TYPES = [('pdf', _('PDF')), ('docx', _('DOCX')), ('odt', _('ODT')), ('ods', _('ODS')), ('xlsx', _('XLSX'))]

class ReportTemplateConfig(models.Model):
    _name = 'report.template.config'
    _description = 'Report Template Config'
    _rec_name = 'name'
    _sql_constraints = [('unique_key', 'unique (key)', 'Key must be unique')]

    template = fields.Many2one('ir.attachment', string='Template')
    file = fields.Binary(string='Template File')
    filename = fields.Char(string='Filename')
    key = fields.Char(string='Template Key')
    name = fields.Char(string='Template Name')
    catagory = fields.Char(string='Category')
    company_id = fields.Many2one('res.company', string='Company')

    parameter_id = fields.Many2one('report.template.parameter', string='Parameter')

    output_type = fields.Selection(OUT_TYPES, default='docx', string='Output type')
    use_python_docx = fields.Boolean(string = 'Use Python Docx',default = False)
    model_id = fields.Selection(selection='_list_all_models', string='Model')
    file_cancel = fields.Binary(string='Template File Cancel')
    password = fields.Char(string='Password')

    @api.model
    def _list_all_models(self):
        self._cr.execute('SELECT model, name FROM ir_model ORDER BY name')
        return self._cr.fetchall()

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        for arg in args:
            if arg[0] == 'id' and arg[1] == 'in':
                tmp = arg[2]
                if not isinstance(tmp, list) and isinstance(tmp, (str)):
                    arg[2] = [int(x) for x in tmp.split(',')]
        domain = []
        records = self.search(domain + args, limit=limit, order='name')
        
        result =[(record.id, record.display_name) for record in records]
        return result

    @api.onchange('file')
    def auto_generate_name(self):
        if self.file:
            self.name = self.filename.replace('.docx', '')

    @api.onchange('name')
    def auto_generate_key(self):
        if self.name and not self.key:
            self.key = self.slugy(self.name)

    @api.model
    def get_template(self):
        return self.file

    def slugy(self, text):
        text = text.lower()
        return re.sub(r'\W+', '_', text)