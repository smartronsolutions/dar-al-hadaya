from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    dah_customization = fields.Text(
        string='Customization',
        help='Free-text customization the customer typed on the website '
             '(what to write, make or personalize).',
    )
    dah_color_theme = fields.Char(
        string='Color Theme',
        help='Color theme chosen or typed by the customer on the website.',
    )

    def _prepare_invoice_line(self, **optional_values):
        values = super()._prepare_invoice_line(**optional_values)
        values.update({
            'dah_customization': self.dah_customization,
            'dah_color_theme': self.dah_color_theme,
        })
        return values


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    dah_customization = fields.Text(string='Customization', copy=True)
    dah_color_theme = fields.Char(string='Color Theme', copy=True)
