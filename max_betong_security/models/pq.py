
from odoo import models, api
from lxml import etree

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options=options)
        if self.env.user.has_group('max_betong_security.group_betong_dvkh'):
            if 'list' in res['views']:
                arch = res['views']['list']['arch']
                doc = etree.XML(arch)
                for node in doc.xpath("//tree"):
                    node.set('create', 'false')
                    node.set('edit', 'false')
                    node.set('delete', 'false')
                res['views']['list']['arch'] = etree.tostring(doc, encoding='unicode')

            if 'form' in res['views']:
                arch = res['views']['form']['arch']
                doc = etree.XML(arch)
                for node in doc.xpath("//form"):
                    node.set('create', 'false')
                    node.set('edit', 'false')
                    node.set('delete', 'false')
                for field in doc.xpath("//field"):
                    field.set('readonly', '1')
                for btn in doc.xpath("//button"):
                    btn.set('invisible', '1')
                res['views']['form']['arch'] = etree.tostring(doc, encoding='unicode')
        return res