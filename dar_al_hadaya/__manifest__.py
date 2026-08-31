{
    'name': 'Dar Al Hadaya',
    'version': '19.0.1.8.0',
    'category': 'Website',
    'summary': 'Dar Al Hadaya - premium mobile-first gifting e-commerce website',
    'description': """
Dar Al Hadaya Website
=====================

Premium, mobile-first gifting e-commerce website for Dar Al Hadaya.

* Mobile-first design: product search, centered logo, WhatsApp and cart icons.
* Homepage: hero/banner slider, horizontally scrollable Shop by Category,
  Featured Gifts, simple 3-step ordering process and a scrolling product
  catalogue (4 products per screen in a 2x2 mobile grid).
* Product page: product video first (vertical 9:16 viewer), image gallery,
  variations, quantity selector, ORDER NOW and WhatsApp buttons, expandable
  sections (Description / Details, contents & size / Product information)
  and a fixed Order Now bar while scrolling.
* Cart / Order sidebar: adds "Add a Little Extra" recommended add-ons,
  shows the full order, total, customer name and WhatsApp number and then
  completes the order on WhatsApp.
* Media rule: Instagram creatives are reused as-is - 4:5 portrait images and
  9:16 Reel videos are never cropped or forced into a different aspect ratio.
* Simplified backend with 6 main areas: Orders, Products, Customers,
  Categories, Website Content and Point of Sale.
""",
    'author': 'Dar Al Hadaya',
    'depends': [
        'website',
        'website_sale',
        'website_sale_wishlist',
        'sale_management',
        'stock',
        'point_of_sale',
    ],
    'data': [
        'data/product_public_categories.xml',
        'views/product_views.xml',
        'views/menus.xml',
        'views/dah_common.xml',
        'views/website_home.xml',
        'views/website_product.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'dar_al_hadaya/static/src/css/dar_al_hadaya.css',
            'dar_al_hadaya/static/src/js/dar_al_hadaya.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
