* REQUIREMENTS *
  Install:
    - py3o.template (0.9.9 or better) An easy solution to design reports using OpenOffice, for basic templating (odt->odt and ods->ods only)
    - genshi (0.7 or better)
    - Unoconv: Convert files to any format that supports LibreOffice. Website: http://dag.wiee.rs/home-made/unoconv/
      Download
      The following packages (in order of appearance) are available.
        Red Hat 
        Debian
        Fedora
        Mandriva
        Ubuntu Lucid
        OpenSUSE


  LibreOffice (Versión: 4.4.6.3 or better). tested with LibreOffice write versión: 4.4.6.3 (Optional for create templates)


Supported output format combinations (Template -> Output):
  odt -> odt(default) odt -> pdf odt -> doc odt -> docx odt -> pds

Note:
  If the program unoconv default output will show in ODT format regardless of the output field you selected in the report is not installed.

Extend and personalize object report example:
```python
    #Object extend
    class sale_oder(models.Model):
        _inherit = "sale.order"

        #Use method
        def custom_report(self):
            obj_precision = self.env['decimal.precision']
            prec = obj_precision.precision_get('Account')
            lines = []
            for item in self.order_line:
                lines.append(
                    {"product": item.name,
                    "qty": int(item.product_uom_qty),
                    "image": item.product_id.image_medium,
                    "price_unit": format(item.price_unit, '.%sf' % prec),
                    "tax": ', '.join(map(lambda x: (x.description or x.name), item.tax_id)),
                    "price_subtotal": format(item.price_subtotal, '.%sf' % prec),
                    })
            values = {
                "order_line": lines,
                "untaxed": format(self.amount_untaxed, '.%sf' % prec),
                "tax": format(self.amount_tax, '.%sf' % prec),
                "total": format(self.amount_total, '.%sf' % prec),
                "symbol": self.pricelist_id.currency_id.symbol
            }
            #Return Dict
            return values
```

XML:
```xml
    <record id="attachment_test_res_users" model="ir.attachment">
        <field name="name">test_res_users.odt</field>
        <field name="type">binary</field>
        <field name="datas" type="base64" file="xb_report_office/templates/test_res_users.odt"/>
    </record>

    <record id="action_report_test_res_users" model="ir.actions.report">
        <field name="name">Test User</field>
        <field name="model">res.users</field>
        <field name="report_type">controller</field>
        <field name="report_name">PrintUser</field>
        <field name="report_file">Print User</field>
        <field name="print_report_name">'USER - %s' % (object.name)</field>
        <field name="attachment_use">False</field>
        <field name="binding_model_id" ref="base.model_res_users"/>
        <field name="binding_type">report</field>
        <field name="template_id" ref="xb_report_office.attachment_test_res_users"/>
    </record>
```

Define field value in document:
  py3o.data.total
  py3o.data.untaxed
  py3o.data.tax



# New Feature:
+ For Vertical: Hidden Column `for` and `/for` in template 
+ Covert Type: 
  - Add Context {"convert": `file_type`}
  - Support:
    all file --> `pdf`
    `ods` <---> `xlsx`
    `odt` <---> `docx`, `doc`
    `docx`, `doc`, `odt` --> `rtf`

  - Not Support;
    `ods`, `xlsx`  <-xxx-> `odt`, `docx`
