import html
import re

from odoo import api, fields, models


_DAH_NAMED_COLORS = {
    'Black': '#000000',
    'White': '#FFFFFF',
    'Midnight Navy': '#132254',
    'Navy': '#000080',
    'Royal Blue': '#4169E1',
    'Sky Blue': '#87CEEB',
    'Teal': '#008080',
    'Green': '#008000',
    'Olive': '#808000',
    'Yellow': '#FFFF00',
    'Gold': '#D4AF37',
    'Orange': '#FFA500',
    'Red': '#FF0000',
    'Maroon': '#800000',
    'Pink': '#FFC0CB',
    'Purple': '#800080',
    'Brown': '#8B4513',
    'Beige': '#F5F5DC',
    'Cream': '#FFFDD0',
    'Grey': '#808080',
    'Silver': '#C0C0C0',
}


def _dah_color_details(value):
    color = (value or '').strip().upper()
    if not re.fullmatch(r'#[0-9A-F]{6}', color):
        label = html.escape(color or 'Not selected')
        return label, label
    rgb = tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))
    name = min(
        _DAH_NAMED_COLORS,
        key=lambda candidate: sum(
            (channel - int(_DAH_NAMED_COLORS[candidate][index:index + 2], 16)) ** 2
            for channel, index in zip(rgb, (1, 3, 5))
        ),
    )
    label = f'{name} ({color})'
    preview = (
        f'<span style="display:inline-block;width:18px;height:18px;border-radius:50%;'
        f'background-color:{color};border:1px solid #aaa;vertical-align:middle;'
        f'margin-right:7px"></span>{html.escape(label)}'
    )
    return label, preview


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
    dah_color_label = fields.Char(string='Color Name', compute='_compute_dah_color_display', store=True)
    dah_color_preview = fields.Html(
        string='Color Theme', compute='_compute_dah_color_display', store=True, sanitize=False,
    )

    @api.depends('dah_color_theme')
    def _compute_dah_color_display(self):
        for line in self:
            line.dah_color_label, line.dah_color_preview = _dah_color_details(line.dah_color_theme)

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
    dah_color_label = fields.Char(string='Color Name', compute='_compute_dah_color_display', store=True)
    dah_color_preview = fields.Html(
        string='Color Theme', compute='_compute_dah_color_display', store=True, sanitize=False,
    )

    @api.depends('dah_color_theme')
    def _compute_dah_color_display(self):
        for line in self:
            line.dah_color_label, line.dah_color_preview = _dah_color_details(line.dah_color_theme)
