import io
import zipfile
import time
import tempfile
import mimetypes
from base64 import standard_b64decode
from py3o.template.main import *
from py3o.template import Template

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.addons.xb_report.models.multi_converter import *


def render_report(report, data, output_file):
    stream = io.BytesIO(standard_b64decode(report.sudo().template_id.datas))
    temp = tempfile.NamedTemporaryFile()
    t = Template(stream, temp)
    t.render(data)
    temp.seek(0)
    if not output_file:
        return False
    out = convert_file(temp.name, report.template_id.mimetype, output_file)
    out = report._set_password(out, output_file, report.password_name, data)
    temp.close()
    return out


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    report_type = fields.Selection(selection_add=[('controller', 'Controller')], ondelete={"controller": "set default"})
    template_id = fields.Many2one("ir.attachment", "Template")
    template_multi_doc = fields.Boolean("Allow render with multi Doc.")
    output_file = fields.Selection([
        ("pdf", "pdf"),
        ("ods", "ods"),
        ("odt", "odt"),
        ("doc", "doc"),
        ("docx", "docx"),
        ("xlsx", "xlsx"),
        ("rtf", "rtf"),
        ], string="Format Output File.", default="odt",
        help='Format Output File. (Format Default *.odt Output File)')

    def render_controller(self, res_ids=[], data=None):
        particularreport_obj = self[0]
        t_report_name = particularreport_obj.name
        assert particularreport_obj.template_id, "Report %s not template file." % t_report_name

        report_obj = self.env[particularreport_obj.model]

        output_file = particularreport_obj.output_file
        docs = report_obj.browse(res_ids)
        report_name = particularreport_obj.name
        if particularreport_obj.print_report_name and not len(docs) > 1:
            report_name = safe_eval(particularreport_obj.print_report_name, {'object': docs})
        '''
            Chú ý:
                report_name=particularreport_obj.report_name
                Một số báo cáo trong 1 model có thể sử dụng nhiều key report name để tách ra nhiều báo cáo
        '''
        if len(res_ids) == 1:
            data = dict(o=docs)
            data.update({"data": docs.with_context(report_name=particularreport_obj.report_name).custom_report()})
            result = render_report(particularreport_obj, data, output_file)
        else:
            buff = io.BytesIO()
            zip_archive = zipfile.ZipFile(buff, mode='w')

            for doc in docs:
                data = dict(o=doc)
                if particularreport_obj.print_report_name:
                    report_name = safe_eval(particularreport_obj.print_report_name, {'object': doc})
                data.update({"data": doc.with_context(report_name=particularreport_obj.report_name).custom_report()})

                out = render_report(particularreport_obj, data, output_file)
                zip_archive.writestr("%s.%s" % (report_name, output_file), out)
            zip_archive.close()
            result = buff.getvalue()
            output_file = "zip"
        return result, output_file

    @api.model
    def _render_controller(self, report_ref, res_ids=None, data=None):
        return self._get_report(report_ref).render_controller(res_ids, data)