import base64
from pathlib import Path

from odoo import api, fields, models
from odoo.fields import Domain


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    dah_navigation_category = fields.Boolean(
        string='Dar Al Hadaya Navigation Category',
        default=False,
        help='Keeps this category available from the global shop navigation, even before products are assigned.',
    )

    @api.depends_context('company', 'website_id')
    def _compute_has_published_products(self):
        super()._compute_has_published_products()
        self.filtered('dah_navigation_category').has_published_products = True

    @api.model
    def _search_has_published_products(self, operator, value):
        product_domain = super()._search_has_published_products(operator, value)
        if product_domain is NotImplemented:
            return product_domain
        return Domain.OR([
            product_domain,
            Domain('dah_navigation_category', '=', True),
        ])

    @api.model
    def _dah_ensure_navigation_categories(self):
        """Ensure matching internal/public categories and migrate safe one-to-one links."""
        category_images = {
            'Islamic Frames': ('islamic frames.png',),
            'Qatar Pin': ('qatar pin.png',),
            '3D Keychain': ('3d keychains.png',),
            'Personalized Frames': ('Personalized Frames.png',),
            'Newborn & Baby Gifts': ('new baby.png',),
            'Graduation Gifts': ('graduation.png',),
            'Wedding & Marriage Gifts': ('wedding.png',),
            'Birthday Gifts': ('birthday.png',),
            'Hajj & Umrah Gifts': ('hall and umrah gifts.png',),
            'Islamic Gifts': ('islamic gifts.png',),
            'Corporate & Business Gifts': ('corporate and buissnes gifts.png',),
            'Jewelry & Premium Gifts': ('jewely and premium gifts.png',),
            # Supporting navigation categories used by the global header.
            'Occasions': (),
            'Custom Gifts': ('custom gifts.png',),
        }
        category_aliases = {
            'Newborn & Baby Gifts': 'New Baby',
            'Graduation Gifts': 'Graduation',
            'Wedding & Marriage Gifts': 'Wedding',
            'Birthday Gifts': 'Birthday',
        }
        image_directory = Path(__file__).resolve().parents[1] / 'static' / 'src' / 'img' / 'categories'
        for category_name, fallback_images in category_images.items():
            public_category = self.search(
                [('name', '=ilike', category_name)],
                order='id',
                limit=1,
            )
            if not public_category and category_name in category_aliases:
                public_category = self.search(
                    [('name', '=ilike', category_aliases[category_name])],
                    order='id',
                    limit=1,
                )
                if public_category:
                    public_category.name = category_name
            if not public_category:
                public_category = self.create({'name': category_name})
            public_category.dah_navigation_category = True
            image_candidates = (f'{category_name.lower()}.png', *fallback_images)
            image_path = next((image_directory / filename for filename in image_candidates if (image_directory / filename).is_file()), None)
            if image_path:
                public_category.image_1920 = base64.b64encode(image_path.read_bytes())

            internal_category = self.env['product.category'].search(
                [('name', '=ilike', category_name)],
                order='id',
                limit=1,
            )
            if not internal_category and category_name in category_aliases:
                internal_category = self.env['product.category'].search(
                    [('name', '=ilike', category_aliases[category_name])],
                    order='id',
                    limit=1,
                )
                if internal_category:
                    internal_category.name = category_name
            if not internal_category:
                internal_category = self.env['product.category'].create({
                    'name': category_name,
                })

            products_to_migrate = self.env['product.template'].search([
                ('categ_id', '=', False),
                ('public_categ_ids', '=', public_category.id),
            ])
            products_to_migrate.with_context(dah_skip_category_sync=True).write({
                'categ_id': internal_category.id,
            })
        return True


class ProductTemplate(models.Model):
    """Dar Al Hadaya product fields.

    Everything the website needs beyond the standard Odoo product: the
    Instagram-style media (4:5 images + 9:16 Reel video), gifting copy and
    merchandising flags. Standard Odoo fields already cover the rest:
    name, price (list_price), SKU (default_code), main photo (image_1920),
    extra photos (product_template_image_ids), variations (attribute lines),
    stock (qty), website category (public_categ_ids), POS category
    (pos_category_ids) and website publication (is_published).
    """

    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        products = super().create(vals_list)
        products._dah_sync_public_category()
        return products

    def write(self, vals):
        result = super().write(vals)
        if 'categ_id' in vals and not self.env.context.get('dah_skip_category_sync'):
            self._dah_sync_public_category()
        return result

    def _dah_sync_public_category(self):
        """Keep one website category aligned with the selected Product Category."""
        PublicCategory = self.env['product.public.category']
        navigation_names = {
            'Islamic Frames', 'Qatar Pin', '3D Keychain', 'Personalized Frames',
            'Newborn & Baby Gifts', 'Graduation Gifts', 'Wedding & Marriage Gifts',
            'Birthday Gifts', 'Hajj & Umrah Gifts', 'Islamic Gifts',
            'Corporate & Business Gifts', 'Jewelry & Premium Gifts',
            'Occasions', 'Custom Gifts',
        }
        for product in self:
            if not product.categ_id:
                product.with_context(dah_skip_category_sync=True).write({
                    'public_categ_ids': [(5, 0, 0)],
                })
                continue

            category_name = product.categ_id.name
            public_category = PublicCategory.search(
                [('name', '=ilike', category_name)],
                order='id',
                limit=1,
            )
            if not public_category:
                public_category = PublicCategory.create({
                    'name': category_name,
                    'dah_navigation_category': category_name in navigation_names,
                })
            product.with_context(dah_skip_category_sync=True).write({
                'public_categ_ids': [(6, 0, public_category.ids)],
            })

    dah_video_url = fields.Char(
        string='Product Video URL',
        help='Direct URL of the product video (Instagram Reel, 9:16 / 1080x1920). '
             'Displayed as the first media on the product page, in its original '
             'vertical proportions.',
    )
    dah_short_description = fields.Html(
        string='Short Introduction',
        help='One or two sentences shown right below the order buttons.',
        sanitize=True,
    )
    dah_details_contents = fields.Html(
        string='Details, Contents & Size',
        help='Expandable "Details, contents & size" section of the product page.',
        sanitize=True,
    )
    dah_product_information = fields.Html(
        string='Product Information',
        help='Expandable "Product information" section of the product page.',
        sanitize=True,
    )
    dah_featured = fields.Boolean(
        string='Featured Product',
        default=False,
        help='Featured gifts are highlighted on the homepage hero slider and the '
             'Featured Gifts section.',
    )
    dah_is_addon = fields.Boolean(
        string='Is Gift Add-on',
        default=False,
        help='Products like greeting cards, premium gift bags or ribbon wrapping. '
             'They are suggested in the "Add a Little Extra" area of the order '
             'sidebar.',
    )
    dah_recommended_addon_ids = fields.Many2many(
        comodel_name='product.template',
        relation='dar_al_hadaya_product_addon_rel',
        column1='product_id',
        column2='addon_id',
        string='Recommended Add-ons',
        help='Suggested add-ons shown in the order sidebar when this product is '
             'in the cart.',
    )
