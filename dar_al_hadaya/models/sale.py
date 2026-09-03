from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    dah_customization = fields.Text(
        string='Customization',
        help='Free-text customization the customer typed on the website '
             '(what to write, make or personalize).',
    )
    def _prepare_invoice_line(self, **optional_values):
        values = super()._prepare_invoice_line(**optional_values)
        values.update({
            'dah_customization': self.dah_customization,
        })
        return values


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    dah_customer_name = fields.Char(string='Website Customer Name', copy=False)
    dah_whatsapp_number = fields.Char(string='WhatsApp Number', copy=False)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    dah_customization = fields.Text(string='Customization', copy=True)
