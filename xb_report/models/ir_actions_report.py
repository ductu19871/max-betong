import logging

from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.modules.module import get_resource_path
from odoo.tools.rendering_tools import parse_inline_template, render_inline_template
from .hash_password_pdf import add_password_pdf
_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    # ------------------------------------------------------------
    # Synchronous report
    # ------------------------------------------------------------
    execution_mode = fields.Selection([
        ('sync', 'Synchronous'),
        ('async', 'Asynchronous'),
    ], required=True, default='sync', string='Execution Mode')
    cron_id = fields.Many2one('ir.cron', 'Scheduled Action', readonly=True)
    fonts = fields.Selection([('arial', 'Arial Regular'), ('arialbd', 'Arial Bold'), ('arialbi', 'Arial Bold Italic'), ('ariali', 'Arial Italic'),
                            ('comic', 'Comic Sans Regular'), ('comicbd', 'Comic Sans Bold'),
                            ('cour', 'Courier New Regular'), ('courbd', 'Courier New Bold'), ('courbi', 'Courier New Bold Italic'), ('couri', 'Courier New Italic'),
                            ('tahoma', 'Tahoma Regular'), ('tahomabd', 'Tahoma Bold'),
                            ('times', 'Times New Roman Regular'), ('timesbd', 'Times New Roman Bold'), ('timesbi', 'Times New Roman Italic'), ('timesi', 'Times New Roman Italic')], string='Fonts') # Current support for Report Fill PDF
    # TODO: support more report types (docx, xlsx, etc)
    password_name = fields.Char("Password", help="Use this field to set password for PDF report. You can use placeholders. Example: {{ context.get('password') }} or {{ 1 + 1 }}")

    @api.model_create_multi
    def create(self, vals_list):
        result = super(IrActionsReport, self).create(vals_list)
        for rec in result:
            rec._update_cron()
        return result

    @api.model
    def _render_password(self, values, password_text):
        if not password_text:
            return ''
        template_instructions = parse_inline_template(password_text)
        is_dynamic = len(template_instructions) > 1 or template_instructions[0][1]
        if is_dynamic:
            password = render_inline_template(template_instructions, values)
        else:
            password = template_instructions[0][0]
        return password

    def _support_password_extensions(self):
        return ['pdf']

    def _set_password(self, content, ext, password_text=None, render_values=None):
        if ext not in self._support_password_extensions():
            return content
        if not password_text:
            password_text = self.password_name
        if not password_text:
            return content

        if render_values:
            password_text = self._render_password(render_values, password_text)

        return add_password_pdf(content, password_text)

    def write(self, vals):
        res = super(IrActionsReport, self).write(vals)
        for rec in self:
            rec._update_cron()
        return res

    def _update_cron(self):
        if self.execution_mode != 'async' and self.cron_id:
            self.cron_id.unlink()
        if self.execution_mode == 'async' and not self.cron_id:
            vals = self._get_cron_vals()
            self.cron_id = self.env['ir.cron'].create(vals)

    def _get_cron_vals(self):
        self.ensure_one()
        return {
            "name": _("Printing %s") % self.name,
            "model_id": self.env.ref("xb_report.model_ir_actions_report_execution").id,
            "state": "code",
            "code": "model.auto_print_report()",
            "user_id": SUPERUSER_ID,
            "active": True,
            "interval_number": 1,
            "interval_type": "minutes",
            "numbercall": -1,
            "doall": False,
            "priority": 15,
        }

    @api.model
    def _render_qweb_html(self, report_ref, docids, data=None):
        if '__pdf_render_context' in self._context:
            self._context['__pdf_render_context']['data'] = data or {}
        return super(IrActionsReport, self)._render_qweb_html(report_ref, docids, data)

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if not self._context.get('force_render_qweb_pdf'):
            self._render_in_asynchronous_mode(report_ref, res_ids, data)

        pdf_render_context = {}
        context = dict(self._context, __pdf_render_context=pdf_render_context)

        pdf, ext = super(IrActionsReport, self.with_context(context))._render_qweb_pdf(report_ref, res_ids, data)

        if not self._context.get('force_disable_password'):
            report_sudo = self._get_report(report_ref)
            data = pdf_render_context.get('data', {})
            pdf = report_sudo._set_password(pdf, ext, render_values=data)
        return pdf, ext

    def _render_in_asynchronous_mode(self, report_ref, res_ids, data):
        if self.execution_mode == 'async':
            # Translate message before creating a new cursor,
            # to avoid error caused by cursor closed
            msg = _("Printing in progress. You will be notified as soon as done.")
            with registry(self._cr.dbname).cursor() as new_cr:
                self = self.with_env(self.env(cr=new_cr))
                self._check_execution(report_ref, res_ids, data)
            raise UserError(msg)

    def _check_execution(self, report_ref, res_ids, data):
        arguments = repr((report_ref, res_ids, data))
        context = repr(self._context)

        execution_obj = self.env['ir.actions.report.execution']
        execution_id = execution_obj.search([
            ('report_id', '=', self.id),
            ('arguments', '=', arguments),
            ('context', '=', context),
            ('state', '!=', 'done'),
        ], limit=1)
        if execution_id:
            execution_id.user_ids |= self.env.user
        else:
            execution_obj.create({
                'report_id': self.id,
                'arguments': arguments,
                'context': context,
            })

    # ------------------------------------------------------------
    # force_disable_report_preview
    # ------------------------------------------------------------
    def report_action(self, docids, data=None, config=True):
        action = super(IrActionsReport, self).report_action(docids, data=data, config=config)
        if self._context.get('force_disable_report_preview') and action.get('type') == 'ir.actions.report':
            action['report_preview'] = False
        return action


    # Support forms in qweb reports
    @api.model
    def _build_wkhtmltopdf_args(
            self,
            paperformat_id,
            landscape,
            specific_paperformat_args=None,
            set_viewport_size=False):
        command_args = super(IrActionsReport, self)._build_wkhtmltopdf_args(paperformat_id, landscape, specific_paperformat_args, set_viewport_size)
        if specific_paperformat_args and specific_paperformat_args.get('data-report-enable-forms'):
            command_args.append('--enable-forms')
        elif paperformat_id and paperformat_id.enable_forms:
            command_args.append('--enable-forms')
        return command_args

    def _get_font_for_reports(self):
        module_path = get_resource_path('xb_report')
        if not self or (self and not self.fonts):
            return module_path + '/fonts/arial/arial.ttf'
        font_path = module_path
        if self.fonts.find('arial') > -1:
            font_path += '/fonts/arial/'
        elif self.fonts.find('comic') > -1:
            font_path += '/fonts/comic_sans/'
        elif self.fonts.find('cour') > -1:
            font_path += '/fonts/courier/'
        elif self.fonts.find('tahoma') > -1:
            font_path += '/fonts/tahoma/'
        elif self.fonts.find('times') > -1:
            font_path += '/fonts/time_new_roman/'
        return font_path + self.fonts + '.ttf'
