import base64
import re
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from odoo import _, api, fields, models
from odoo.fields import Domain


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def _dah_configure_shop_layout(self):
        """Keep the Dar Al Hadaya catalogue at four columns and 20 items."""
        website = self.env.ref('website.default_website', raise_if_not_found=False)
        if website:
            website.write({'shop_ppr': 4, 'shop_ppg': 20})
        return True

    @staticmethod
    def _get_product_sort_mapping():
        """Use the customer-facing wording requested for the main shop sort."""
        return [
            ('website_sequence asc', _('Best Selling')),
            ('publish_date desc', _('Newest Arrivals')),
            ('name asc', _('Name (A-Z)')),
            ('list_price asc', _('Price - Low to High')),
            ('list_price desc', _('Price - High to Low')),
        ]


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    dah_for_dar_al_hadaya = fields.Boolean(
        string='For Dar Al Hadaya',
        default=False,
        index=True,
        help='Show this category automatically in the Dar Al Hadaya homepage Shop by Category section.',
    )

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
        home_seed_names = {
            'Islamic Frames', 'Qatar Pin', '3D Keychain', 'Personalized Frames',
            'Newborn & Baby Gifts', 'Graduation Gifts', 'Wedding & Marriage Gifts',
            'Birthday Gifts', 'Hajj & Umrah Gifts', 'Islamic Gifts',
            'Corporate & Business Gifts', 'Jewelry & Premium Gifts',
        }
        migration_key = 'dar_al_hadaya.home_category_flag_initialized'
        config = self.env['ir.config_parameter'].sudo()
        initialize_home_flags = not config.get_param(migration_key)

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
            if initialize_home_flags and category_name in home_seed_names:
                public_category.dah_for_dar_al_hadaya = True
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
        if initialize_home_flags:
            config.set_param(migration_key, '1')
        return True


class DarAlHadayaOccasion(models.Model):
    _name = 'dah.occasion'
    _description = 'Gift Occasion'
    _order = 'sequence, name, id'

    name = fields.Char(required=True, translate=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='dah_product_template_occasion_rel',
        column1='occasion_id',
        column2='product_tmpl_id',
        string='Products',
    )
    product_count = fields.Integer(compute='_compute_product_count')

    _name_unique = models.Constraint('UNIQUE(name)', 'An occasion with this name already exists.')

    @api.depends('product_ids')
    def _compute_product_count(self):
        for occasion in self:
            occasion.product_count = len(occasion.product_ids)


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

    dah_occasion_ids = fields.Many2many(
        comodel_name='dah.occasion',
        relation='dah_product_template_occasion_rel',
        column1='product_tmpl_id',
        column2='occasion_id',
        string='Occasions',
        help='Occasions used by the customer-facing Shop filter and navigation.',
    )
    dah_occasion = fields.Char(
        string='Legacy Occasion',
        copy=False,
        help='Previous fixed occasion value retained only for safe data migration.',
    )

    def init(self):
        """Move values from the former Selection field into manageable records."""
        self.env.cr.execute("""
            SELECT column_name
              FROM information_schema.columns
             WHERE table_name = 'product_template' AND column_name = 'dah_occasion'
        """)
        if not self.env.cr.fetchone():
            return
        self.env.cr.execute("""
            SELECT DISTINCT dah_occasion
              FROM product_template
             WHERE dah_occasion IS NOT NULL AND dah_occasion != ''
        """)
        legacy_values = [row[0] for row in self.env.cr.fetchall()]
        legacy_labels = {
            'ramadan': 'Ramadan', 'eid': 'Eid', 'baby_shower': 'Baby Shower',
            'engagement': 'Engagement', 'housewarming': 'Housewarming',
        }
        Occasion = self.env['dah.occasion'].with_context(active_test=False)
        for legacy_value in legacy_values:
            occasion_name = legacy_labels.get(legacy_value, legacy_value.replace('_', ' ').title())
            occasion = Occasion.search([('name', '=ilike', occasion_name)], limit=1)
            if not occasion:
                occasion = Occasion.create({'name': occasion_name})
            self.env.cr.execute("""
                INSERT INTO dah_product_template_occasion_rel (product_tmpl_id, occasion_id)
                SELECT product.id, %s
                  FROM product_template AS product
                 WHERE product.dah_occasion = %s
                   AND NOT EXISTS (
                       SELECT 1 FROM dah_product_template_occasion_rel AS relation
                        WHERE relation.product_tmpl_id = product.id
                          AND relation.occasion_id = %s
                   )
            """, (occasion.id, legacy_value, occasion.id))
    dah_personalized = fields.Boolean(
        string='Personalization',
        index=True,
        help='Enable this when the product can be personalized. Customers can filter these products on the Shop page.',
    )

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
        help='YouTube, Instagram Reel/Post or Facebook video URL. The video is '
             'displayed as the first media on the product page.',
    )
    dah_video_type = fields.Selection(
        selection=[('link', 'Link'), ('upload', 'Upload')],
        string='Video Type',
        default='link',
        required=True,
    )
    dah_video_file = fields.Binary(
        string='Upload Video',
        attachment=True,
        help='Upload an MP4/WebM video owned by your business.',
    )
    dah_video_filename = fields.Char(string='Video Filename')

    def _dah_video_data(self):
        """Describe the first gallery video selected by the product manager."""
        self.ensure_one()
        if self.dah_video_type == 'upload' and self.dah_video_file:
            return {
                'type': 'upload',
                'url': f'/dah/product/video/{self.id}',
            }
        if self.dah_video_type != 'upload':
            embed_url = self._dah_video_embed_url()
            if embed_url:
                return {'type': 'embed', 'url': embed_url}
        return False

    def _dah_video_embed_url(self):
        """Return a safe embed URL for supported public video providers."""
        self.ensure_one()
        raw_url = (self.dah_video_url or '').strip()
        if not raw_url:
            return False
        parsed = urlparse(raw_url if '://' in raw_url else f'https://{raw_url}')
        host = (parsed.hostname or '').lower().removeprefix('www.')
        video_id = ''
        if host == 'youtu.be':
            video_id = parsed.path.strip('/').split('/')[0]
        elif host in {'youtube.com', 'm.youtube.com', 'youtube-nocookie.com'}:
            if parsed.path == '/watch':
                video_id = parse_qs(parsed.query).get('v', [''])[0]
            else:
                parts = [part for part in parsed.path.split('/') if part]
                if len(parts) >= 2 and parts[0] in {'embed', 'shorts', 'live'}:
                    video_id = parts[1]
        if re.fullmatch(r'[A-Za-z0-9_-]{6,20}', video_id or ''):
            return (
                f'https://www.youtube-nocookie.com/embed/{video_id}'
                '?autoplay=1&mute=1&playsinline=1&rel=0'
            )

        if host in {'instagram.com', 'm.instagram.com'}:
            parts = [part for part in parsed.path.split('/') if part]
            if len(parts) >= 2 and parts[0] in {'reel', 'reels', 'p', 'tv'}:
                media_type = 'reel' if parts[0] == 'reels' else parts[0]
                media_code = parts[1]
                if re.fullmatch(r'[A-Za-z0-9_-]{5,40}', media_code):
                    return f'https://www.instagram.com/{media_type}/{media_code}/embed/'

        facebook_hosts = {
            'facebook.com', 'm.facebook.com', 'web.facebook.com',
            'fb.watch', 'fb.com',
        }
        if host in facebook_hosts and parsed.path.strip('/'):
            safe_url = quote(raw_url, safe='')
            return (
                'https://www.facebook.com/plugins/video.php'
                f'?href={safe_url}&show_text=false&autoplay=true&mute=true'
            )
        return False

    def _dah_youtube_embed_url(self):
        """Compatibility alias retained for previously compiled templates."""
        return self._dah_video_embed_url()
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

    def _dah_legacy_rating_distribution(self):
        """Return the per-star review breakdown for the product page.

        Returns a list of dicts ordered from 5 stars down to 1::

            [{'stars': 5, 'count': 40, 'percentage': 70}, ...]

        Percentages are rounded integers; a product without reviews yields an
        all-zero distribution. Public visitors get the data through ``sudo`` so
        the website can render the review bars anonymously.
        """
        self.ensure_one()
        counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        total = self.rating_count or 0
        if total:
            rating_model = self.env['rating.rating'].sudo()
            groups = rating_model.read_group(
                [
                    ('res_model', '=', self._name),
                    ('res_id', '=', self.id),
                    ('consumed', '=', True),
                    ('rating', '>=', 1),
                ],
                ['rating'],
                ['rating'],
            )
            for group in groups:
                value = group.get('rating')
                if not value:
                    continue
                star = min(5, max(1, int(round(value))))
                counts[star] += int(group.get('rating_count', 0))
        return [
            {
                'stars': star,
                'count': counts[star],
                'percentage': round(counts[star] * 100.0 / total) if total else 0,
            }
            for star in (5, 4, 3, 2, 1)
        ]
