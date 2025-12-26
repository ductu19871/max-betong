from odoo.http import Controller, route, request, content_disposition

class ReportDocx(Controller):

    @route('/web/mailmerge_report', type='http', auth="user")
    def send_reports_mail_merge_docx(self, res_model, res_id, template_id, report_name, **kargs):
        model = request.env[res_model].with_context(output_type=kargs.get('output_type', False)).browse(int(res_id))
        file, file_name, output_type = model.action_get_mail_merge_reports(template_id, report_name, kargs.get('password', False))

        headers = [('Content-Length', len(file))]
        if output_type == 'docx':
            headers.extend([
                ('Content-Disposition', content_disposition(file_name + '.docx')),
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            ])
        elif output_type == 'odt':
            headers.extend([
                ('Content-Disposition', content_disposition(file_name + '.odt')),
                ('Content-Type', 'application/vnd.oasis.opendocument.text'),
            ])
        elif output_type == 'pdf':
            headers.extend([
                ('Content-Disposition', content_disposition(file_name + '.pdf')),
                ('Content-Type', 'application/pdf'),
            ])

        return request.make_response(file, headers=headers)
