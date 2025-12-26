from odoo import api, fields, models, registry, Command, _
from odoo.tools.misc import unquote
from odoo.tools.safe_eval import safe_eval
import time, base64
from markupsafe import Markup

# ------------------------------------------------------------
# Create new TransientModel report.execution
# ------------------------------------------------------------
class IrActionsReportExecution(models.TransientModel):
    _name = 'ir.actions.report.execution'
    _description = 'Asynchronous Printing'
    _inherit = 'mail.thread'
    _rec_name = 'create_date'
    _order = 'create_date desc'

    create_uid = fields.Many2one('res.users', 'Created by', readonly=True)
    create_date = fields.Datetime('Created On', readonly=True)
    report_id = fields.Many2one('ir.actions.report',
                                'Report',
                                required=True,
                                ondelete='cascade',
                                readonly=True)
    arguments = fields.Text(readonly=True)
    context = fields.Text(readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             string='State',
                             required=True,
                             readonly=True,
                             copy=False,
                             default='draft')
    time = fields.Float(readonly=True, string='Time')
    attachment_id = fields.Many2one('ir.attachment',
                                    string='Attachment',
                                    compute='_get_attachment')
    user_ids = fields.Many2many('res.users', string='User Following')

    @api.depends('state')
    def _get_attachment(self):
        for rec in self:
            rec.attachment_id = self.env['ir.attachment'].search([
                ('res_model', '=', rec._name),
                ('res_id', '=', rec.id),
            ], limit=1)

    @api.model
    def auto_print_report(self):
        for record in self.search([('state', '=', 'draft')]):
            record.with_user(record.create_uid.id).print_report()
        return True

    def print_report(self):
        self.ensure_one()
        report = self.report_id
        args = safe_eval(self.arguments)
        ctx = self._eval_context()
        ctx['force_render_qweb_pdf'] = True
        attachments = []
        t0 = time.time()
        try:
            report_name = report.name
            content, ext = report.with_context(ctx)._render_qweb_pdf(*args)

            attachments = [(report_name, content)]
            msg = _('%s report available') % report_name
        except Exception as e:
            msg = _('%s printing failed') % report_name
        finally:
            # INFO: use a new cursor to:
            # 1. avoid concurrent updates
            # 2. have access to the whole list of followers
            # if some followers were added during printing
            with registry(self._cr.dbname).cursor() as new_cr:
                self = self.with_env(self.env(cr=new_cr))
                self.write({
                    'time': time.time() - t0,
                    'state': 'done',
                })
                self.sudo()._send_notification(msg, attachments)
            return True

    def _eval_context(self):
        self.ensure_one()
        eval_dict = {
            'active_id': unquote("active_id"),
            'active_ids': unquote("active_ids"),
            'active_model': unquote("active_model"),
            'uid': self.create_uid.id,
            'context': self._context,
        }
        return safe_eval(self.context, eval_dict)
    
    def _send_notification(self, msg, attachments=None):
        kwargs = self._get_message_post_arguments(msg, attachments)
        for user in self.create_uid | self.user_ids:
            channel_id = self._get_channel(user)
            if channel_id:
                channel_id.message_post(**kwargs)

    def _get_message_post_arguments(self, msg, attachments):
        return {
            'author_id': self.env['ir.model.data']._xmlid_to_res_id("base.partner_root"),
            'email_from': False,  # To avoid to get author from email data
            'body': Markup(msg) if msg else False,
            'message_type': 'comment',
            'subtype_xmlid': 'mail.mt_comment',
            'attachments': attachments,
        }
    
    def _get_channel(self, user):
        self.ensure_one()
        channel_id = False
        system_user = self._get_system_user()
        if user.id in system_user.ids:
            return channel_id
        
        partner_ids = (user | system_user).mapped('partner_id')
        channel = False
        if partner_ids:
            discuss_channel_ids = self.env['discuss.channel.member'].sudo().search([('partner_id', 'in', partner_ids.ids),
                                                                                    ('channel_id.channel_type', '=', 'group')])
            if discuss_channel_ids:
                channel_ids = discuss_channel_ids.mapped('channel_id')
                for rec_chan_id in channel_ids:
                    # list(set([1, 2, 5, 6]) & set([1, 2])) == [1, 2] --> get
                    if len(list(set(rec_chan_id.channel_member_ids.mapped('partner_id.id')) & \
                                set(partner_ids.ids))) == len(partner_ids.ids):
                        channel = rec_chan_id.id
                        break
        
        if channel:
            channel_id = self.env['discuss.channel'].browse(channel)
            return channel_id
        
        if not channel_id and partner_ids:
            channel_id = self.env['discuss.channel'].create({
                'name': ', '.join(partner_ids.mapped('name')),
                'channel_type': 'group',
                'channel_member_ids': [(0, 0, {'partner_id': item}) for item in partner_ids.ids]
            })
        return channel_id
    
    def _get_system_user(self):
        result = self.env.ref('base.group_system').mapped('users')
        return result