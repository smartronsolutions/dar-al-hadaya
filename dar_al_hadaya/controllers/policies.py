from odoo import http
from odoo.http import request


class DarAlHadayaPolicies(http.Controller):
    """Public, indexable legal-information pages linked from the footer."""

    @http.route('/terms-conditions', type='http', auth='public', website=True, sitemap=True)
    def terms_and_conditions(self, **kwargs):
        return request.render('dar_al_hadaya.dah_policy_terms')

    @http.route('/terms', type='http', auth='public', website=True, sitemap=False)
    def legacy_terms_redirect(self, **kwargs):
        return request.redirect('/terms-conditions', code=301)

    @http.route('/privacy', type='http', auth='public', website=True, sitemap=True)
    def privacy_policy(self, **kwargs):
        return request.render('dar_al_hadaya.dah_policy_privacy')

    @http.route('/refund-policy', type='http', auth='public', website=True, sitemap=True)
    def refund_policy(self, **kwargs):
        return request.render('dar_al_hadaya.dah_policy_refund')
