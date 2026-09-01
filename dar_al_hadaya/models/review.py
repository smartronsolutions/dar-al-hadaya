from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DahProductReview(models.Model):
    _name = 'dah.product.review'
    _description = 'Dar Al Hadaya Product Review'
    _order = 'create_date desc, id desc'

    product_tmpl_id = fields.Many2one(
        'product.template', string='Product', required=True, ondelete='cascade', index=True,
    )
    partner_id = fields.Many2one('res.partner', string='Customer', ondelete='set null')
    name = fields.Char(string='Reviewer', required=True, default='Guest')
    rating = fields.Integer(string='Stars', required=True, default=5)
    comment = fields.Text(string='Review', required=True)
    active = fields.Boolean(default=True)

    @api.constrains('rating')
    def _check_rating(self):
        for review in self:
            if review.rating < 1 or review.rating > 5:
                raise ValidationError('Rating must be between 1 and 5 stars.')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def dah_public_reviews(self, limit=50):
        self.ensure_one()
        return self.env['dah.product.review'].sudo().search([
            ('product_tmpl_id', '=', self.id), ('active', '=', True),
        ], limit=limit)

    def dah_review_stats(self):
        self.ensure_one()
        reviews = self.dah_public_reviews(limit=0)
        count = len(reviews)
        average = sum(reviews.mapped('rating')) / count if count else 0.0
        return {'count': count, 'average': average}

    def dah_rating_distribution(self):
        self.ensure_one()
        reviews = self.dah_public_reviews(limit=0)
        total = len(reviews)
        counts = {star: 0 for star in range(1, 6)}
        for review in reviews:
            counts[review.rating] += 1
        return [{
            'stars': star,
            'count': counts[star],
            'percentage': round(counts[star] * 100.0 / total) if total else 0,
        } for star in (5, 4, 3, 2, 1)]
