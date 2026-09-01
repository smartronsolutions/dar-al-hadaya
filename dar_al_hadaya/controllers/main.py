from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
from odoo.tools import html2plaintext


class DarAlHadayaWebsiteSale(WebsiteSale):
    """Add simple, client-manageable Occasion and Personalization filters."""

    def _get_search_options(self, **kwargs):
        options = super()._get_search_options(**kwargs)
        try:
            product_category_id = int(request.httprequest.args.get('product_category', 0))
        except (TypeError, ValueError):
            product_category_id = 0
        options['dah_product_category_id'] = product_category_id
        occasion_values = request.httprequest.args.getlist('occasion')
        occasion_ids = [int(value) for value in occasion_values if value.isdigit()]
        options['dah_occasions'] = request.env['dah.occasion'].sudo().search([
            ('id', 'in', occasion_ids), ('active', '=', True),
        ]).ids
        options['dah_personalized'] = request.httprequest.args.get('personalized') == '1'
        return options

    def _shop_lookup_products(self, options, post, search, website):
        fuzzy_search_term, product_count, products = super()._shop_lookup_products(
            options, post, search, website
        )
        extra_domain = []
        if options.get('dah_product_category_id'):
            extra_domain.append(('categ_id', 'child_of', options['dah_product_category_id']))
        if options.get('dah_occasions'):
            extra_domain.append(('dah_occasion_ids', 'in', options['dah_occasions']))
        if options.get('dah_personalized'):
            extra_domain.append(('dah_personalized', '=', True))
        if extra_domain:
            products = products.filtered_domain(extra_domain)
            product_count = len(products)
        return fuzzy_search_term, product_count, products

    def _shop_get_query_url_kwargs(
        self, search, min_price, max_price, order=None, tags=None, **kwargs
    ):
        values = super()._shop_get_query_url_kwargs(
            search, min_price, max_price, order=order, tags=tags, **kwargs
        )
        occasions = request.httprequest.args.getlist('occasion')
        product_category = request.httprequest.args.get('product_category')
        if product_category:
            values['product_category'] = product_category
        if occasions:
            values['occasion'] = occasions
        if request.httprequest.args.get('personalized') == '1':
            values['personalized'] = '1'
        return values


class DarAlHadayaWebsite(http.Controller):
    """Frontend helpers for the Dar Al Hadaya website.

    The customer journey stays mostly client-side (the order sidebar builds
    the WhatsApp message), but the cart data is read from Odoo's own cart
    (a draft sale.order created by website_sale), so every order is also
    recorded in the backend Orders area.
    """

    @http.route('/dah/product/suggestions', type='jsonrpc', auth='public', website=True, readonly=True)
    def product_suggestions(self, term='', limit=6):
        """Return lightweight suggestions from products visible on this website."""
        term = (term or '').strip()
        if len(term) < 2:
            return {'results': []}
        try:
            limit = min(max(int(limit), 1), 10)
        except (TypeError, ValueError):
            limit = 6
        website = request.website
        products = request.env['product.template'].sudo().search(
            website.sale_product_domain() + [('name', 'ilike', term)],
            order='website_sequence asc, name asc',
            limit=limit,
        )
        currency = website.currency_id
        results = []
        for product in products:
            amount = product.list_price
            price = (
                f'{amount:,.2f} {currency.symbol}'
                if currency.position == 'after'
                else f'{currency.symbol} {amount:,.2f}'
            )
            results.append({
                'name': product.name,
                'website_url': product.website_url,
                'image_url': request.website.image_url(product, 'image_128'),
                'detail': price,
            })
        return {'results': results}

    @http.route('/dah/cart/data', type='jsonrpc', auth='public', website=True, methods=['POST'])
    def cart_data(self):
        order = request.cart
        currency = (order and order.currency_id) or request.website.currency_id
        result = {
            'count': 0,
            'amount_total': 0.0,
            'order_reference': order.name if order else '',
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
                'sku': product.default_code or template.default_code or '',
                'description': html2plaintext(template.dah_short_description or '').strip(),
                'image_src': request.website.image_url(product, 'image_256'),
                'price': line.price_unit,
                'subtotal': line.price_subtotal,
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
        return {'number': '9743344765'}
