from odoo import fields, models, api, _
from io import BytesIO
import qrcode
import base64
from odoo.tools.misc import formatLang, format_date, format_datetime, format_amount
from functools import partial
from .common import amount_to_text_vn, BLANK_IMAGE
import json


class Base(models.AbstractModel):
    _inherit = 'base'

    def custom_report(self):
        result = super().custom_report()
        result['_tools_']['amount_to_text_vn'] = amount_to_text_vn
        result['BLANK_IMAGE'] = BLANK_IMAGE
        return result

    # TODO: general function get qr code
    def get_qr_code(self, name, version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=1.5, border=0.5, fill_color="black", back_color="white"):
        byte_io_data = BytesIO()
        qr = qrcode.QRCode(
            version=version,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border
        )
        qr.add_data(name or '')
        qr.make(fit=True)

        qr_code_data_img = qr.make_image(fill_color=fill_color, back_color=back_color)
        qr_code_data_img.save(byte_io_data)
        byte_io_data.seek(0)
        qr_binary = byte_io_data.read()
        
        return base64.b64encode(qr_binary)

    @api.model
    def _get_alias_report_phrase(self, key, default_value=''):
        params = self.env['ir.config_parameter'].sudo()
        sources = json.loads(params.get_param('alias_report_phrase_realm', '{}'))
        return sources.get(key, default_value)