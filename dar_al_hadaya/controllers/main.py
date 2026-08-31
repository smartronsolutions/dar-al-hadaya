from odoo import http
from odoo.http import request


class DarAlHadayaWebsite(http.Controller):
    """Frontend helpers for the Dar Al Hadaya website.

    The customer journey stays mostly client-side (the order sidebar builds
    the WhatsApp message), but the cart data is read from Odoo's own cart
    (a draft sale.order created by website_sale), so every order is also
    recorded in the backend Orders area.
    """

    @http.route('/dah/cart/data', type='jsonrpc', auth='public', website=True, methods=['POST'])
    def cart_data(self):
        order = request.cart
        currency = (order and order.currency_id) or request.website.currency_id
        result = {
            'count': 0,
            'amount_total': 0.0,
            'currency_symbol': currency.symbol,
            'currency_position': currency.position,
            'currency_rounding': currency.rounding,
            'lines': [],
            'addons': [],
        }

        if not order or not order.order_line:
            return result

        lines = order.order_line.filtered(lambda line: not line.display_type)
        result['count'] = sum(int(line.product_uom_qty) for line in lines)
        result['amount_total'] = currency.round(order.amount_total)

        for line in lines:
            product = line.product_id
            template = product.product_tmpl_id
            attributes = line.product_no_variant_attribute_value_ids | line.product_id.product_template_attribute_value_ids
            result['lines'].append({
                'line_id': line.id,
                'product_id': product.id,
                'name': template.name,
                'image_src': request.website.image_url(product, 'image_256'),
                'price': line.price_unit,
                'qty': line.product_uom_qty,
                'attributes': ', '.join(attributes.mapped('name')),
                'url': template.website_url,
            })

        result['addons'] = self._get_cart_addons(order)
        return result

    def _get_cart_addons(self, order):
        """"Add a Little Extra" suggestions for the order sidebar.

        Combines the recommended add-ons of the products already in the cart
        with every product flagged as a gift add-on (greeting card, premium
        gift bag, ribbon wrapping...). Products already in the cart are
        excluded.
        """
        website = request.website
        in_cart_lines = order.order_line.filtered(lambda line: not line.display_type)
        in_cart_tmpl_ids = set(in_cart_lines.product_id.product_tmpl_id.ids)

        recommended = in_cart_lines.product_id.product_tmpl_id.dah_recommended_addon_ids
        flagged = request.env['product.template'].search([
            ('dah_is_addon', '=', True),
            ('sale_ok', '=', True),
            ('active', '=', True),
        ])
        addon_templates = (recommended | flagged).filtered(
            lambda t: t.id not in in_cart_tmpl_ids and t.filtered_domain(website.sale_product_domain())
        ).sorted(key=lambda t: t.name)

        addons = []
        for template in addon_templates:
            variant = template.product_variant_id
            addons.append({
                'product_id': variant.id,
                'template_id': template.id,
                'name': template.name,
                'price': variant.list_price,
                'image_src': request.website.image_url(template, 'image_256'),
                'url': template.website_url,
            })
        return addons

    @http.route('/dah/whatsapp', type='jsonrpc', auth='public', website=True, methods=['POST'])
    def whatsapp_info(self):
        """Return the WhatsApp number used to complete orders."""
        icp = request.env['ir.config_parameter'].sudo()
        number = icp.get_param('dar_al_hadaya.whatsapp_number', '') or ''
        number = number.replace(' ', '').replace('-', '').replace('+', '')
        company = request.website.company_id
        if not number:
            number = (company.phone or '').replace(' ', '').replace('-', '').replace('+', '')
        return {'number': number}
