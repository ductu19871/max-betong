from odoo import models, fields, api
from datetime import datetime
import base64
from mailmerge import MailMerge
from io import BytesIO
from . import multi_converter
from . import qr_code
from .hash_password_pdf import add_password_pdf
from zipfile import ZipFile, BadZipfile
import re
from genshi.template import MarkupTemplate
from genshi.output import TextSerializer
from lxml.etree import Element
import codecs
import logging
from functools import partial
from odoo.tools import html2plaintext
from odoo.tools.misc import formatLang, format_date, format_datetime, format_amount, format_duration
from .common import amount_to_text
from .multi_converter import convert_file
from py3o.template import Template
from base64 import standard_b64decode
import tempfile
import base64
_logger = logging.getLogger(__name__)

NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
}

class CustomMailMerge(MailMerge):

    def __merge_pythoncode(self, parts, data):
        for part in parts:
            for mfunc in part.findall('.//MergeField'):
                text = mfunc.attrib.get('name', False) or ''
                expression = re.findall(r'\${[^\${}]*}', text)

                if len(expression):
                    # xoa field mailmerge tren report
                    children = list(mfunc)
                    mfunc.clear()
                    mfunc.tag = '{%(w)s}r' % NAMESPACES
                    mfunc.extend(children)
                    # Thay value vao doi tuong
                    nodes = []
                    for item in expression:
                        template = MarkupTemplate('<span>' + item + '</span>')
                        stream = template.generate(data=data)
                        result = stream.render(TextSerializer, strip_markup=True)
                        text = text.replace(item, result)

                    text_node = Element('{%(w)s}t' % NAMESPACES)
                    text_node.text = text
                    nodes.append(text_node)

                    ph = mfunc.find('MergeText')
                    if ph is not None:
                        index = mfunc.index(ph)
                        for node in reversed(nodes):
                            mfunc.insert(index, node)
                        mfunc.remove(ph)
                    else:
                        mfunc.extend(nodes)


    def __merge_function(self, parts, data):
        for part in parts:
            for mfunc in part.findall('.//MergeField[@name="function"]'):
                ph = mfunc.find('MergeText')
                if ph is not None:
                    # Lay bieu thuc tinh trong python
                    text = codecs.decode(ph.text, 'unicode_escape')
                    expression = re.findall(r'\${[^\${}]*}', text)
                    result = ''
                    for item in expression:
                        template = MarkupTemplate('<span>' + item + '</span>')
                        stream = template.generate(data=data)
                        result += stream.render(TextSerializer, strip_markup=True)
                    # thay the ket qua
                    nodes = []
                    text_node = Element('{%(w)s}t' % NAMESPACES)
                    text_node.text = result
                    nodes.append(text_node)
                    index = mfunc.index(ph)
                    for node in reversed(nodes):
                        mfunc.insert(index, node)
                    mfunc.remove(ph)
            for mfunc in part.findall('.//MergeField[@name="pfunction"]'):
                ph = mfunc.find('MergeText')
                if ph is not None:
                    # Lay bieu thuc tinh trong python
                    expression = re.findall(r'\${[^\${}]*}', ph.text)
                    result = ''
                    for item in expression:
                        template = MarkupTemplate('<span>' + item + '</span>')
                        stream = template.generate(data=data)
                        result += stream.render(TextSerializer, strip_markup=True)
                    # thay the ket qua
                    nodes = []
                    text_node = Element('{%(w)s}t' % NAMESPACES)
                    text_node.text = result
                    nodes.append(text_node)
                    index = mfunc.index(ph)
                    for node in reversed(nodes):
                        mfunc.insert(index, node)
                    mfunc.remove(ph)

    def merge(self, parts=None, **replacements):
        if not parts:
            parts = self.parts.values()
        self.__merge_function(parts, replacements)
        self.__merge_pythoncode(parts, replacements)
        super(CustomMailMerge, self).merge(parts, **replacements)



class Base(models.AbstractModel):
    _inherit = 'base'

    def _get_custom_report_supported_context_tools(self):
        return {
            'formatLang': partial(formatLang, self.env),
            'format_date': partial(format_date, self.env),
            'format_datetime': partial(format_datetime, self.env),
            'format_amount': partial(format_amount, self.env),
            'format_duration': partial(format_duration),
            'amount_to_text': amount_to_text,
            'html2plaintext': html2plaintext,
        }

    def custom_report(self):
        return {
            '_object_': self,
            '_user_': self.env.user,
            '_tools_': self._get_custom_report_supported_context_tools()
        }

    @api.model
    def get_data_export(self):

        list_fields = self._fields
        result = {
            '__obj__': self,
            'obj': self,
            '_tools_': self._get_custom_report_supported_context_tools()
        }
        # bypass security for export
        self = self.sudo()
        for key, value in list_fields.items():
            list_type = ['char', 'selection',
                        'boolean', 'float',
                        'text', 'integer',
                        'date', 'datetime',
                        'html', 'many2one',
                        'monetary']
            if value.type in list_type:
                if value.type == 'selection':
                    if not self[value.name] or self[value.name] == '':
                        result.update({
                            key: '',
                        })
                    else:
                        dict_selection = False
                        if value.related_field:
                            dict_selection = dict(value.related_field._description_selection(self.env))
                        else:
                            dict_selection = dict(value._description_selection(self.env))
                        if dict_selection:
                            result.update({
                                key: dict_selection[self[value.name]] or '',
                            })
                elif value.type == 'many2one':
                    result.update({
                        key: self[value.name].display_name if self[value.name] else '',
                    })
                elif value.type == 'date':
                    result.update({
                        key: format_date(self.env, self[value.name]) if self[value.name] else '',
                    })
                elif value.type == 'datetime':
                    country_code = self._context.get('lang') or self.env.user.lang or 'en_US'
                    current_country = self.env['res.lang'].search([('code', '=', country_code)])
                    date_time = current_country.date_format + ' ' + current_country.time_format
                    result.update({
                        key: self[value.name].strftime(date_time) if self[value.name] else '',
                    })
                elif value.type == 'boolean':
                    result.update({
                        key: str(self[value.name]),
                    })
                elif value.type == 'monetary':
                    result.update({
                        key: str(formatLang(self.env, self[value.name], monetary=True, currency_obj=self.env.user.company_id.currency_id)) if self[value.name] else '',
                    })
                else:
                    result.update({
                        key: str(self[value.name]) if self[value.name] else '',
                    })
        return result

    @api.model
    def parse_split_date(self, key):
        # Convert to 'dd', 'mm', 'yyyy'
        data = {}
        if key == None:
            date_today = fields.Date.today()
            data.update({'dd': date_today.strftime('%d')})
            data.update({'mm': date_today.strftime('%m')})
            data.update({'yyyy': date_today.strftime('%Y')})
            return data
        data = {key + '_dd': '', key + '_mm': '', key + '_yyyy': ''}
        if self[key]:
            data.update({key + '_dd': self[key].strftime('%d')})
            data.update({key + '_mm': self[key].strftime('%m')})
            data.update({key + '_yyyy': self[key].strftime('%Y')})
        return data
    
    def action_get_mail_merge_reports(self, template_id, report_name, hash_password=''):
        new_context = dict(self._context or {})
        new_context.update({'template_id': int(template_id)})
        kwargs = self.with_context(new_context).get_data_export()
        template_obj = self.env['report.template.config'].browse(int(template_id))
        output_type = self._context.get('output_type', False) or template_obj.output_type
        filename = ""
        if output_type in ('xlsx', 'ods'):
            data = dict(o=self)
            data.update({"data": self.custom_report()})
            stream = BytesIO(standard_b64decode(template_obj.file))
            temp = tempfile.NamedTemporaryFile()
            t = Template(stream, temp)
            t.render(data)
            out = convert_file(temp.name, 'application/vnd.oasis.opendocument.spreadsheet', output_type)
            stream = out
            filename = template_obj.name
        else:
            if 'state' in kwargs and kwargs.get('state', '') in ('cancel', 'cancelled') and template_obj.file_cancel:
                file_content = BytesIO(base64.decodebytes(template_obj.file_cancel))
            else:
                file_content = BytesIO(base64.decodebytes(template_obj.file))
            if template_obj.use_python_docx: 
                file_content = self.get_data_python_docx(file_content)
            # QR Code
            if kwargs and 'qr_code' in kwargs:
                try:
                    generate_qr_code = qr_code.XBQRCode(2, 1, kwargs['qr_code'], file_content)
                    #Check zipfile qr
                    ZipFile(generate_qr_code.write_file())
                    file_content = generate_qr_code.write_file()
                except BadZipfile as e:
                    _logger.warning(e)
                    pass
            
            document = CustomMailMerge(file_content)
            document.merge(**kwargs)
            if kwargs.get('tables'):
                for anchor, rows in kwargs.get('tables').items():
                    document.merge_rows(anchor, rows)
            file_data = BytesIO()
            document.write(file_data)
            file_data.seek(0)
            stream = file_data.read()

            if output_type != 'docx':
                stream = multi_converter.convert_multiple_file(stream, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', None, format='binary', mime_export=output_type)

            # Generate password pdf file
            if not hash_password and template_obj and template_obj.password:
                hash_password = template_obj.password
            if output_type == 'pdf' and hash_password:
                stream = add_password_pdf(BytesIO(stream), hash_password)

            now = datetime.now()
            filename = report_name + '_%s_%s_%s' % (str(now.day), str(now.month), str(now.year))

        return stream, filename, output_type