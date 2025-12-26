import json, io, zipfile, logging
from py3o.template.main import *
from werkzeug.urls import url_decode
from odoo.tools.safe_eval import safe_eval

from odoo.tools import html_escape
from odoo.http import request, serialize_exception, content_disposition
from odoo.addons.xb_report_office.models.report import render_report
from odoo import http
from odoo.addons.web.controllers.report import ReportController as RC
from odoo.addons.xb_report.models.multi_converter import *

_logger = logging.getLogger(__name__)

MIME_DICT = {
    "odt": "application/vnd.oasis.opendocument.text",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "rtf": "application/rtf",
    "zip": "application/zip",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

def make_response(mimetype, content, file_name, out_format_file):
    headers = [
        ('Content-Type', mimetype),
        ('Content-Length', len(content)),
        ('Content-Disposition', content_disposition("%s.%s" % (file_name,out_format_file)))
    ]
    return request.make_response(content, headers=headers)


class ReportControllerExtend(RC):
    @http.route()
    def report_download(self, data, context=None, token=None):
        requestcontent = json.loads(data)
        url, report_type = requestcontent[0], requestcontent[1]
        if report_type != "controller":
            return super().report_download(data, context=context, token=token)

        try:
            t_report_name = url.split("/report/report_office_controller/")[1].split("?")[0]
            docids = None
            if "/" in t_report_name:
                t_report_name, docids = t_report_name.split("/")
            if docids and type(docids) == str:
                docids = [int(i) for i in docids.split(",")]

            # Reupdate string context to dict
            if context:
                context = json.loads(context)
            context.update(dict(request.env.context))
            if not docids or docids is None:
                url_data = dict(url_decode(url.split("?")[1]).items())
                if "context" in url_data:
                    context.update(json.loads(url_data.get('context', {})))
            context.update({'report_name': t_report_name})

            Report = request.env['ir.actions.report']
            conditions = [
                ('report_type', 'in', ['controller']),
                ('report_name', '=', t_report_name)]
            report_ids = Report.search(conditions)
            assert report_ids, 'Not found report name ' + t_report_name

            particularreport_obj = report_ids[0]
            assert particularreport_obj.template_id, "Report %s not template file." % t_report_name

            report_obj = request.env[particularreport_obj.model]

            output_file = particularreport_obj.output_file
            if context.get('r_convert'):
                output_file = context.get('r_convert')
            assert output_file, "Not found output file"

            docs = report_obj.browse(docids)
            report_name = particularreport_obj.name
            zip_filename = report_name
            if particularreport_obj.print_report_name and not len(docs) > 1:
                report_name = safe_eval(particularreport_obj.print_report_name, {'object': docs})

            if len(docids) == 1 or particularreport_obj.template_multi_doc:
                data = dict(o=docs)
                # The custom_report method must return a dictionary
                # If any model has method custom_report
                if hasattr(report_obj, 'custom_report'):
                    data.update({"data": docs.with_context(context).custom_report()})
                out = render_report(particularreport_obj, data, output_file)
                return make_response(MIME_DICT[output_file], out, report_name, output_file)
            # if more than one zip returns
            else:
                # This is where my zip will be written
                buff = io.BytesIO()
                # This is my zip file
                zip_archive = zipfile.ZipFile(buff, mode='w')

                for doc in docs:
                    data = dict(o=doc)
                    if particularreport_obj.print_report_name:
                        report_name = safe_eval(particularreport_obj.print_report_name, {'object': doc})
                    # The custom_report method must return a dictionary
                    # If any model has method custom_report
                    if hasattr(report_obj, 'custom_report'):
                        data.update({"data": doc.with_context(context).custom_report()})

                    out = render_report(particularreport_obj, data, output_file)
                    zip_archive.writestr("%s.%s" % (report_name, output_file), out)
                # You can visualize the structure of the zip with this command
                # print zip_archive.printdir()
                zip_archive.close()
                return make_response(MIME_DICT["zip"], buff.getvalue(), zip_filename, "zip")

        except Exception as e:
            _logger.exception("Error while generating report %s", t_report_name)
            error = {"code": 200, "message": "Odoo Server Error", "data": serialize_exception(e)}
            return request.make_response(html_escape(json.dumps(error)))