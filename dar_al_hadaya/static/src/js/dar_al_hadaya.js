/* ════════════════════════════════════════════════════════════════════
   DAR AL HADAYA frontend JS
   Header, mobile menu, order sidebar, WhatsApp order flow, hero slider,
   wishlist and the product-page helpers.
   ════════════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    function dahRpc(url, params, jsonRoute) {
        // jsonRoute = true  -> simple {params} body (type='json' routes)
        // jsonRoute = false -> jsonrpc envelope (jsonrpc routes)
        const body = jsonRoute
            ? JSON.stringify({params: params || {}})
            : JSON.stringify({jsonrpc: '2.0', method: 'call', params: params || {}});
        return fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: body,
        })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error.message || data.error.data && data.error.data.message || 'Request failed');
                }
                return data.result;
            });
    }

    function money(amount, data) {
        if (amount === null || amount === undefined) { return '–'; }
        const value = Number(amount).toFixed(2);
        const sym = data.currency_symbol || '';
        return data.currency_position === 'after' ? value + ' ' + sym : sym + ' ' + value;
    }

    const DahWebsite = {
        waNumber: '9743344765',

        /* ── helpers ──────────────────────────────────────────── */
        $: function (sel) { return document.querySelector(sel); },
        $$: function (sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); },

        init: function () {
            this.header();
            this.whatsapp();
            this.footer();
            this.cart();
            this.heroSlider();
            this.categoryScroller();
            this.wishlist();
            this.lowerNav();
            this.productPage();
            this.shopFilters();
        },

        shopFilters: function () {
            this.$$('[data-dah-filter-url]').forEach(input => {
                input.addEventListener('change', () => {
                    window.location.href = input.dataset.dahFilterUrl;
                });
            });
            this.$$('.dah-shop-sidebar-sort select').forEach(select => {
                select.addEventListener('change', () => {
                    window.location.href = select.value;
                });
            });
        },

        /* ── header: hamburger menu toggle + Escape ───────────── */
        header: function () {
            const headerEl = this.$('#dah_site_header');
            const menuBtn = this.$('#dah_menu_btn');
            const menuClose = this.$('#dah_menu_close');
            const menuOverlay = this.$('#dah_menu_overlay');
            if (!headerEl || !menuBtn) { return; }

            const setMenu = (open) => {
                headerEl.classList.toggle('open', open);
                document.body.classList.toggle('dah-menu-open', open);
                menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
                menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
            };
            menuBtn.addEventListener('click', event => {
                event.preventDefault();
                event.stopPropagation();
                setMenu(!headerEl.classList.contains('open'));
            });
            if (menuClose) { menuClose.addEventListener('click', () => setMenu(false)); }
            if (menuOverlay) { menuOverlay.addEventListener('click', () => setMenu(false)); }
            const dockSearch = this.$('#dah_mobile_dock_search');
            const dockSearchPanel = this.$('#dah_mobile_dock_search_panel');
            if (dockSearch && dockSearchPanel) {
                dockSearch.addEventListener('click', event => {
                    event.stopPropagation();
                    const open = !dockSearchPanel.classList.contains('dah-open');
                    dockSearchPanel.classList.toggle('dah-open', open);
                    window.setTimeout(() => {
                        const input = this.$('#dah_dock_search_input');
                        if (open && input) { input.focus(); }
                    }, 80);
                });
            }
            headerEl.querySelectorAll('.dah-nav a').forEach(link => link.addEventListener('click', () => setMenu(false)));
            headerEl.querySelectorAll('.dah-mobile-submenu-toggle').forEach(toggle => {
                toggle.addEventListener('click', () => {
                    const group = toggle.closest('.dah-mobile-nav-group');
                    if (!group) { return; }
                    headerEl.querySelectorAll('.dah-mobile-nav-group.dah-open').forEach(openGroup => {
                        if (openGroup !== group) {
                            openGroup.classList.remove('dah-open');
                            const openToggle = openGroup.querySelector('.dah-mobile-submenu-toggle');
                            if (openToggle) { openToggle.setAttribute('aria-expanded', 'false'); }
                        }
                    });
                    const open = !group.classList.contains('dah-open');
                    group.classList.toggle('dah-open', open);
                    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
                });
            });

            const plainText = value => {
                const parsed = new DOMParser().parseFromString(String(value || ''), 'text/html');
                return (parsed.body.textContent || '').trim();
            };
            const suggestionClosers = [];
            const setupProductSearch = (inputSelector, suggestionsSelector) => {
                const searchInput = this.$(inputSelector);
                const suggestions = this.$(suggestionsSelector);
                if (!searchInput || !suggestions) { return; }
                let searchTimer;
                let searchRequest = 0;
                const hideSuggestions = () => {
                    suggestions.classList.remove('dah-show');
                    suggestions.replaceChildren();
                };
                suggestionClosers.push(hideSuggestions);
                const renderSuggestions = data => {
                    suggestions.replaceChildren();
                    const results = data && data.results || [];
                    if (!results.length) {
                        const empty = document.createElement('div');
                        empty.className = 'dah-mobile-search-empty';
                        empty.textContent = 'No products found';
                        suggestions.appendChild(empty);
                    }
                    results.forEach(product => {
                        const link = document.createElement('a');
                        link.className = 'dah-mobile-search-result';
                        link.href = plainText(product.website_url) || '/shop';
                        link.setAttribute('role', 'option');
                        const image = document.createElement('img');
                        const rawImageUrl = String(product.image_url || '');
                        const imageDoc = new DOMParser().parseFromString(rawImageUrl, 'text/html');
                        const sourceImage = imageDoc.querySelector('img');
                        image.src = (rawImageUrl.charAt(0) === '/' && rawImageUrl) || (sourceImage && sourceImage.getAttribute('src')) || '/web/static/img/placeholder.png';
                        image.alt = '';
                        const name = document.createElement('span');
                        name.className = 'dah-mobile-search-result-name';
                        name.textContent = plainText(product.name);
                        const price = document.createElement('span');
                        price.className = 'dah-mobile-search-result-price';
                        price.textContent = plainText(product.detail);
                        link.append(image, name, price);
                        suggestions.appendChild(link);
                    });
                    suggestions.classList.add('dah-show');
                };
                searchInput.addEventListener('input', () => {
                    window.clearTimeout(searchTimer);
                    const term = searchInput.value.trim();
                    if (term.length < 2) { hideSuggestions(); return; }
                    const requestId = ++searchRequest;
                    searchTimer = window.setTimeout(() => {
                        dahRpc('/dah/product/suggestions', {term: term, limit: 6}, false).then(data => {
                            if (requestId === searchRequest && searchInput.value.trim() === term) { renderSuggestions(data); }
                        }).catch(hideSuggestions);
                    }, 220);
                });
                searchInput.addEventListener('focus', () => {
                    if (suggestions.childElementCount) { suggestions.classList.add('dah-show'); }
                });
            };
            setupProductSearch('#dah_mobile_search_input', '#dah_mobile_search_suggestions');
            setupProductSearch('#dah_desktop_search_input', '#dah_desktop_search_suggestions');
            setupProductSearch('#dah_dock_search_input', '#dah_dock_search_suggestions');
            document.addEventListener('click', event => {
                if (!event.target.closest('.dah-mobile-search, .dah-desktop-search, .dah-mobile-dock-search-panel')) {
                    suggestionClosers.forEach(close => close());
                    if (dockSearchPanel) { dockSearchPanel.classList.remove('dah-open'); }
                }
            });
            document.addEventListener('keydown', e => {
                if (e.key === 'Escape') {
                    suggestionClosers.forEach(close => close());
                    if (dockSearchPanel) { dockSearchPanel.classList.remove('dah-open'); }
                    setMenu(false);
                }
            });
        },

        /* ── whatsapp links ───────────────────────────────────── */
        whatsapp: function () {
            const waLink = 'https://wa.me/' + this.waNumber;
            ['#dah_wa_link', '#dah_mobile_wa_link', '#dah_footer_wa_link', '#dah_footer_social_wa', '#dah_hero_wa'].forEach(sel => {
                const el = this.$(sel);
                if (el) { el.href = waLink; }
            });
        },

        footer: function () {
            const year = this.$('#dah_footer_year');
            if (year) { year.textContent = String(new Date().getFullYear()); }

            this.$$('.dah_footer_toggle').forEach(toggle => {
                toggle.addEventListener('click', () => {
                    const group = toggle.closest('.dah_footer_group');
                    if (!group) { return; }
                    this.$$('.dah_footer_group.dah_open').forEach(openGroup => {
                        if (openGroup !== group) {
                            openGroup.classList.remove('dah_open');
                            const openToggle = openGroup.querySelector('.dah_footer_toggle');
                            if (openToggle) { openToggle.setAttribute('aria-expanded', 'false'); }
                        }
                    });
                    const open = !group.classList.contains('dah_open');
                    group.classList.toggle('dah_open', open);
                    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
                });
            });

            const backTop = this.$('#dah_back_top');
            if (backTop) {
                const updateBackTop = () => backTop.classList.toggle('dah_show', window.scrollY > 250);
                window.addEventListener('scroll', updateBackTop, {passive: true});
                backTop.addEventListener('click', () => window.scrollTo({top: 0, behavior: 'smooth'}));
                updateBackTop();
            }
        },

        /* ── cart badge + order sidebar ───────────────────────── */
        cart: function () {
            const sidebar = this.$('#dah_cart_sidebar');
            const overlay = this.$('#dah_cart_overlay');
            const cartBtn = this.$('#dah_cart_btn');
            const closeBtn = this.$('#dah_cart_close');
            const continueBtn = this.$('#dah_continue_shopping');

            if (!sidebar) { return; }

            const open = () => {
                sidebar.classList.add('dah_open');
                overlay.classList.add('dah_open');
                document.body.style.overflow = 'hidden';
                this.refreshCart();
            };
            const close = () => {
                sidebar.classList.remove('dah_open');
                overlay.classList.remove('dah_open');
                document.body.style.overflow = '';
            };
            this.openCart = open;
            this.closeCart = close;

            if (cartBtn) {
                cartBtn.addEventListener('click', event => {
                    event.preventDefault();
                    event.stopPropagation();
                    open();
                });
            }
            const dockCart = this.$('#dah_mobile_dock_cart');
            if (dockCart) {
                dockCart.addEventListener('click', event => {
                    event.preventDefault();
                    open();
                });
            }
            if (closeBtn) { closeBtn.addEventListener('click', close); }
            if (continueBtn) { continueBtn.addEventListener('click', close); }
            if (overlay) { overlay.addEventListener('click', close); }

            // Place Order -> WhatsApp
            const placeBtn = this.$('#dah_place_order');
            if (placeBtn) { placeBtn.addEventListener('click', () => this.placeOrder()); }

            // delegate: qty buttons + addons + remove (re-render keeps old nodes)
            const itemsBox = this.$('#dah_cart_items');
            const addonsBox = this.$('#dah_cart_addons');
            if (itemsBox) {
                itemsBox.addEventListener('click', e => {
                    const btn = e.target.closest('[data-dah-qty]');
                    if (!btn) { return; }
                    const lineId = parseInt(btn.dataset.dahLine, 10);
                    const delta = parseInt(btn.dataset.dahQty, 10);
                    const qtyEl = btn.closest('.dah_qty');
                    const current = qtyEl ? parseInt(qtyEl.dataset.qty, 10) : 1;
                    const newQty = Math.max(0, current + delta);
                    if (newQty === 0) {
                        this.updateLine(lineId, 0);
                    } else {
                        this.updateLine(lineId, newQty);
                    }
                });
            }
            if (addonsBox) {
                addonsBox.addEventListener('click', e => {
                    const btn = e.target.closest('[data-dah-addon]');
                    if (!btn) { return; }
                    const productId = parseInt(btn.dataset.dahAddon, 10);
                    const templateId = parseInt(btn.dataset.dahTemplate, 10);
                    this.addProduct(productId, templateId);
                });
            }

            // Auto-open the sidebar after adding a product on the product page.
            document.addEventListener('submit', e => {
                const form = e.target;
                if (!form || !form.classList.contains('js_main_product')) { return; }
                setTimeout(() => {
                    this.refreshCart().then(() => this.openCart()).catch(() => {});
                }, 900);
            });

            this.refreshCart();
        },

        refreshCart: function () {
            return dahRpc('/dah/cart/data', {}, true)
                .then(data => this.renderCart(data))
                .catch(() => {});
        },

        renderCart: function (data) {
            const badge = this.$('#dah_cart_badge');
            if (badge) { badge.textContent = data.count; }

            const itemsBox = this.$('#dah_cart_items');
            const addonsBox = this.$('#dah_cart_addons');
            const totalEl = this.$('#dah_cart_total');

            if (!itemsBox) { return; }
            if (!data.lines || !data.lines.length) {
                itemsBox.innerHTML = '<div class="dah_cart_empty">Your order is empty.</div>';
                const extras = this.$('#dah_cart_extras');
                if (extras) { extras.style.display = 'none'; }
            } else {
                itemsBox.innerHTML = data.lines.map(line => `
                    <div class="dah_cart_line">
                        <a href="${line.url}"><img src="${line.image_src}" alt=""/></a>
                        <div class="dah_cart_line_info">
                            <b>${line.name}</b>
                            <span>${line.attributes || ''}</span>
                            <div class="dah_qty" data-qty="${line.qty}">
                                <button type="button" data-dah-qty="-1" data-dah-line="${line.line_id}" aria-label="Decrease">−</button>
                                <span>${line.qty}</span>
                                <button type="button" data-dah-qty="1" data-dah-line="${line.line_id}" aria-label="Increase">+</button>
                            </div>
                        </div>
                        <div class="dah_cart_line_meta">
                            <span class="dah_cart_line_price">${money(line.price, data)}</span>
                        </div>
                    </div>`).join('');
                const extras = this.$('#dah_cart_extras');
                if (extras) { extras.style.display = data.addons && data.addons.length ? '' : 'none'; }
            }

            if (addonsBox) {
                addonsBox.innerHTML = (data.addons || []).map(addon => `
                    <div class="dah_addon">
                        <img src="${addon.image_src}" alt=""/>
                        <div class="dah_addon_info">
                            <b>${addon.name}</b>
                            <span>${money(addon.price, data)}</span>
                        </div>
                        <button type="button" class="dah_addon_btn" data-dah-addon="${addon.product_id}" data-dah-template="${addon.template_id}" aria-label="Add ${addon.name}">+</button>
                    </div>`).join('');
            }

            if (totalEl) { totalEl.textContent = money(data.amount_total, data); }
        },

        updateLine: function (lineId, quantity) {
            dahRpc('/shop/cart/update', {line_id: lineId, quantity: quantity})
                .then(() => this.refreshCart())
                .catch(err => { console.error(err); this.refreshCart(); });
        },

        addProduct: function (productId, templateId) {
            dahRpc('/shop/cart/add', {
                product_template_id: templateId,
                product_id: productId,
                quantity: 1,
            })
                .then(() => this.refreshCart())
                .catch(err => { console.error(err); this.refreshCart(); });
        },

        placeOrder: function () {
            if (!this.waNumber) {
                const msg = 'Dar Al Hadaya WhatsApp number is not configured yet. Set "dar_al_hadaya.whatsapp_number" in Settings → Technical → System Parameters.';
                if (typeof window.alert === 'function') { window.alert(msg); }
                return;
            }
            dahRpc('/dah/cart/data', {}, true).then(data => {
                const name = (this.$('#dah_customer_name') || {}).value || '';
                const phone = (this.$('#dah_customer_phone') || {}).value || '';

                const lines = (data.lines || []).map((line, index) => {
                    const productUrl = new URL(line.url || '/shop', window.location.origin).href;
                    const details = [
                        `*${index + 1}. ${line.name}*`,
                        line.sku ? `SKU: ${line.sku}` : '',
                        line.attributes ? `Options: ${line.attributes}` : '',
                        line.description ? `Details: ${line.description}` : '',
                        `Quantity: ${line.qty}`,
                        `Unit Price: ${money(line.price, data)}`,
                        `Line Total: ${money(line.subtotal, data)}`,
                        `Product Link: ${productUrl}`,
                    ];
                    return details.filter(Boolean).join('\n');
                });
                let msg = 'Hello Dar Al Hadaya!\n\n*New Order Request*\n';
                if (data.order_reference) { msg += `Order Reference: ${data.order_reference}\n`; }
                if (lines.length) { msg += '\n' + lines.join('\n\n') + '\n'; }
                msg += '\n*Order Total: ' + money(data.amount_total, data) + '*';
                if (name || phone) { msg += '\n\n*Customer Details*'; }
                if (name) { msg += '\nName: ' + name; }
                if (phone) { msg += '\nWhatsApp: ' + phone; }
                msg += '\n\nPlease confirm availability and order details. Thank you!';

                window.open('https://wa.me/' + this.waNumber + '?text=' + encodeURIComponent(msg), '_blank');
            }).catch(() => {});
        },

        /* ── hero slider ───────────────────────────────────────── */
        heroSlider: function () {
            const slider = this.$('#dah_hero_slider');
            if (!slider) { return; }
            const slides = Array.prototype.slice.call(slider.querySelectorAll('.dah_hero_slide'));
            const dots = this.$$('.dah_hero_dot');
            const previous = this.$('#dah_hero_prev');
            const next = this.$('#dah_hero_next');
            if (!slides.length) { return; }

            let current = 0;
            let timer = null;
            const show = (i) => {
                current = (i + slides.length) % slides.length;
                slides.forEach((s, idx) => s.classList.toggle('dah_hero_slide_active', idx === current));
                dots.forEach((d, idx) => d.classList.toggle('dah_hero_dot_active', idx === current));
            };
            const stop = () => { if (timer) { window.clearInterval(timer); timer = null; } };
            const start = () => {
                stop();
                if (slides.length > 1) { timer = window.setInterval(() => show(current + 1), 3000); }
            };
            dots.forEach((dot, index) => dot.addEventListener('click', () => { show(index); start(); }));
            if (previous) { previous.addEventListener('click', () => { show(current - 1); start(); }); }
            if (next) { next.addEventListener('click', () => { show(current + 1); start(); }); }
            slider.addEventListener('mouseenter', stop);
            slider.addEventListener('mouseleave', start);
            slider.addEventListener('focusin', stop);
            slider.addEventListener('focusout', start);
            document.addEventListener('visibilitychange', () => document.hidden ? stop() : start());
            start();
        },

        categoryScroller: function () {
            const rail = this.$('#dah_cat_scroll');
            if (!rail) { return; }

            let autoPaused = false;
            let autoPosition = rail.scrollLeft;
            let resumeTimer = null;
            let dragging = false;

            const pauseAuto = () => {
                autoPaused = true;
                if (resumeTimer) { window.clearTimeout(resumeTimer); resumeTimer = null; }
            };
            const resumeAuto = (delay) => {
                if (resumeTimer) { window.clearTimeout(resumeTimer); }
                resumeTimer = window.setTimeout(() => {
                    // Never let the autoplay resume while a mouse drag is
                    // still in progress (e.g. mouseleave fired mid-drag).
                    if (dragging) { return; }
                    autoPosition = rail.scrollLeft;
                    autoPaused = false;
                }, delay || 0);
            };

            // Arrow buttons.
            this.$$('[data-dah-cat-scroll]').forEach(button => {
                button.addEventListener('click', () => {
                    pauseAuto();
                    const direction = Number(button.dataset.dahCatScroll) || 1;
                    const tile = rail.querySelector('.dah_cat_tile');
                    const step = tile ? tile.getBoundingClientRect().width + 20 : Math.max(180, rail.clientWidth * 0.45);
                    rail.scrollBy({left: direction * step * 2, behavior: 'smooth'});
                    resumeAuto(2200);
                });
            });

            // Mouse drag (desktop only). Touch devices use the native
            // overflow-x scroll, so swiping stays smooth and reliable.
            let moved = false;
            let startX = 0;
            let startScroll = 0;
            rail.addEventListener('pointerdown', event => {
                if (event.pointerType !== 'mouse' || event.button !== 0) { return; }
                dragging = true;
                moved = false;
                startX = event.clientX;
                startScroll = rail.scrollLeft;
                pauseAuto();
                try { rail.setPointerCapture(event.pointerId); } catch (err) {}
            });
            rail.addEventListener('pointermove', event => {
                if (!dragging) { return; }
                const dx = event.clientX - startX;
                if (!moved && Math.abs(dx) > 4) {
                    moved = true;
                    rail.classList.add('dah_dragging');
                }
                if (moved) { rail.scrollLeft = startScroll - dx; }
            });
            const endDrag = event => {
                if (!dragging) { return; }
                dragging = false;
                rail.classList.remove('dah_dragging');
                if (rail.hasPointerCapture(event.pointerId)) { rail.releasePointerCapture(event.pointerId); }
                resumeAuto(1800);
            };
            rail.addEventListener('pointerup', endDrag);
            rail.addEventListener('pointercancel', endDrag);
            rail.addEventListener('lostpointercapture', () => {
                if (!dragging) { return; }
                dragging = false;
                rail.classList.remove('dah_dragging');
                resumeAuto(1200);
            });
            // Don't let a completed drag trigger the tile links.
            rail.addEventListener('click', event => {
                if (!moved) { return; }
                event.preventDefault();
                event.stopPropagation();
                moved = false;
            }, true);

            // Convert a vertical mouse wheel over the rail into a horizontal pan.
            rail.addEventListener('wheel', event => {
                if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) { return; }
                if (rail.scrollWidth <= rail.clientWidth) { return; }
                event.preventDefault();
                rail.scrollLeft += event.deltaY;
                pauseAuto();
                resumeAuto(1800);
            }, {passive: false});

            // Pause the autoplay while a touch user scrolls natively.
            rail.addEventListener('touchstart', pauseAuto, {passive: true});
            rail.addEventListener('touchend', () => resumeAuto(1800), {passive: true});
            rail.addEventListener('mouseenter', pauseAuto);
            rail.addEventListener('mouseleave', () => resumeAuto(600));
            rail.addEventListener('focusin', pauseAuto);
            rail.addEventListener('focusout', () => resumeAuto(600));

            // Autoplay (ping-pong).
            let autoDirection = 1;
            let previousFrame = 0;
            const autoScroll = timestamp => {
                if (!previousFrame) { previousFrame = timestamp; }
                const elapsed = Math.min(timestamp - previousFrame, 50);
                previousFrame = timestamp;
                const maxScroll = rail.scrollWidth - rail.clientWidth;
                if (!autoPaused && !dragging && !document.hidden && maxScroll > 1) {
                    autoPosition += autoDirection * elapsed * 0.018;
                    if (autoPosition >= maxScroll) {
                        autoPosition = maxScroll;
                        autoDirection = -1;
                    } else if (autoPosition <= 0) {
                        autoPosition = 0;
                        autoDirection = 1;
                    }
                    rail.scrollLeft = Math.round(autoPosition);
                }
                window.requestAnimationFrame(autoScroll);
            };
            window.requestAnimationFrame(autoScroll);
        },

        /* ── wishlist ──────────────────────────────────────────── */
        wishlist: function () {
            const btns = this.$$('.dah_wishlist_btn');
            if (!btns.length) { return; }

            dahRpc('/shop/wishlist/get_product_ids', {}, false)
                .then(ids => {
                    const idSet = new Set(ids || []);
                    btns.forEach(btn => {
                        const card = btn.closest('.dah_product_card');
                        if (card && idSet.has(parseInt(card.dataset.productId, 10))) {
                            btn.classList.add('dah_wished');
                        }
                    });
                })
                .catch(() => {});

            btns.forEach(btn => {
                btn.addEventListener('click', e => {
                    e.preventDefault();
                    e.stopPropagation();
                    const card = btn.closest('.dah_product_card');
                    if (!card) { return; }
                    const productId = parseInt(card.dataset.productId, 10);
                    const wished = btn.classList.contains('dah_wished');
                    if (wished) {
                        // remove first entry of this product from the wishlist
                        dahRpc('/shop/wishlist/get_product_ids', {}, false).then(ids => {
                            const id = (ids || []).find(x => x === productId);
                            if (!id) { return; }
                            return dahRpc('/shop/wishlist/remove/' + id, {}, false);
                        }).then(() => btn.classList.remove('dah_wished')).catch(() => {});
                    } else {
                        dahRpc('/shop/wishlist/add', {product_id: productId}, false)
                            .then(() => btn.classList.add('dah_wished'))
                            .catch(() => {});
                    }
                });
            });
        },

        /* ── homepage fixed lower nav ──────────────────────────── */
        lowerNav: function () {
            const lowerNav = this.$('#dah_lower_nav');
            const scrollTopBtn = this.$('#dah_scroll_top');
            if (lowerNav) {
                const onScroll = () => {
                    const y = window.scrollY;
                    const trigger = Math.max(320, document.body.scrollHeight * 0.28);
                    lowerNav.classList.toggle('dah_visible', y > trigger);
                };
                window.addEventListener('scroll', onScroll, {passive: true});
                onScroll();
            }
            if (scrollTopBtn) {
                scrollTopBtn.addEventListener('click', () => window.scrollTo({top: 0, behavior: 'smooth'}));
            }
        },

        /* ── product page helpers ──────────────────────────────── */
        productPage: function () {
            // WhatsApp "Ask about this product"
            this.$$('.dah_wa_product_btn').forEach(btn => {
                btn.addEventListener('click', e => {
                    e.preventDefault();
                    if (!this.waNumber) {
                        const msg = 'Dar Al Hadaya WhatsApp number is not configured yet. Set "dar_al_hadaya.whatsapp_number" in Settings → Technical → System Parameters.';
                        if (typeof window.alert === 'function') { window.alert(msg); }
                        return;
                    }
                    const name = btn.dataset.dahProductName || '';
                    const url = btn.dataset.dahProductUrl || window.location.href;
                    const text = `Hello Dar Al Hadaya! I am interested in "${name}" (${url}). Is it available?`;
                    window.open('https://wa.me/' + this.waNumber + '?text=' + encodeURIComponent(text), '_blank');
                });
            });

            // Fixed "Order Now" bar while scrolling the product page
            const bar = this.$('#dah_fixed_order_bar');
            if (bar) {
                const detail = document.querySelector('#product_detail');
                const onScroll = () => {
                    if (!detail) { return; }
                    const rect = detail.getBoundingClientRect();
                    const past = rect.bottom < window.innerHeight;
                    const nearTop = rect.top > -120;
                    bar.classList.toggle('dah_visible', past && !nearTop);
                };
                window.addEventListener('scroll', onScroll, {passive: true});
                onScroll();
            }
        },
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => DahWebsite.init(), {once: true});
    } else {
        DahWebsite.init();
    }
})();
