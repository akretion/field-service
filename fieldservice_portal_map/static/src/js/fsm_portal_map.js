/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";
import {rpc} from "@web/core/network/rpc";
import {loadJS, loadCSS} from "@web/core/assets";

publicWidget.registry.FsmPortalMapSwitcher = publicWidget.Widget.extend({
    selector: ".o_portal",
    events: {
        "click #fsm_btn_view_list": "_onShowList",
        "click #fsm_btn_view_map": "_onShowMap",
    },

    async start() {
        await this._super(...arguments);
        this.mapInitialized = false;
        this.map = null;
        this.$("#fsm_btn_view_list, #fsm_btn_view_map").attr("type", "button");
    },

    _onShowList(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        this.$("#fsm_btn_view_map").removeClass("active");
        this.$("#fsm_btn_view_list").addClass("active");

        this.$(
            '.o_portal_table, .table-responsive, h3, h4, h5, h6, [class*="orders_"]'
        ).removeClass("d-none");
        this.$("#fsm_portal_map_container").addClass("d-none");
    },

    async _onShowMap(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        this.$("#fsm_btn_view_list").removeClass("active");
        this.$("#fsm_btn_view_map").addClass("active");

        this.$(
            '.o_portal_table, .table-responsive, h3, h4, h5, h6, [class*="orders_"]'
        ).addClass("d-none");
        this.$("#fsm_portal_map_container").removeClass("d-none");

        if (!this.mapInitialized) {
            await this._initMap();
        } else if (this.map) {
            setTimeout(() => {
                this.map.invalidateSize();
            }, 100);
        }
    },

    async _loadLeaflet() {
        if (window.L) return true;

        try {
            // Adjustment according to the actual OCA directory structure (static/lib/leaflet/...)
            await Promise.all([
                loadCSS("/web_leaflet_lib/static/lib/leaflet/leaflet.css"),
                loadJS("/web_leaflet_lib/static/lib/leaflet/leaflet.js"),
            ]);
            return true;
        } catch (error) {
            throw new Error("Impossible de charger la librairie Leaflet locale d'Odoo");
        }
    },

    async _initMap() {
        const canvas = this.$("#fsm_portal_map_canvas")[0];
        if (!canvas) return;

        try {
            await this._loadLeaflet();
        } catch (e) {
            console.error(e);
            canvas.innerHTML =
                '<div class="p-4 text-center text-danger">Erreur : Moteur cartographique indisponible.</div>';
            return;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const rpcParams = {
            search: urlParams.get("search") || "",
            search_in: urlParams.get("search_in") || "all",
            filterby: urlParams.get("filterby") || "open",
        };

        try {
            const data = await rpc("/my/fsm_orders/map_data", rpcParams);

            if (!data || !data.orders || data.orders.length === 0) {
                canvas.innerHTML =
                    '<div class="p-4 text-center text-muted">Aucune intervention géolocalisée trouvée.</div>';
                return;
            }

            canvas.innerHTML = "";

            // Default basic initialization
            this.map = window.L.map(canvas).setView(
                [data.orders[0].lat, data.orders[0].lng],
                13
            );
            this.mapInitialized = true;

            window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap contributors",
            }).addTo(this.map);

            const markersGroup = new window.L.featureGroup();

            // Creation of a single individual marker per work order
            data.orders.forEach((order) => {
                const popupContent = `
                    <div style="min-width: 200px;">
                        <h6 class="mb-1"><a href="/my/fsm_order/${order.id}"><strong>${order.name}</strong></a></h6>
                        <span class="badge bg-info text-white mb-2">${order.stage}</span><br/>
                        <strong>Lieu :</strong> <small>${order.location}</small>
                        ${order.desc ? `<hr class="my-1"/><p class="text-muted small">${order.desc}</p>` : ""}
                    </div>
                `;
                const marker = window.L.marker([order.lat, order.lng]).bindPopup(
                    popupContent
                );
                markersGroup.addLayer(marker);
            });

            markersGroup.addTo(this.map);

            // Dynamic map bounds adjustment to display ALL distinct markers
            if (data.orders.length > 1) {
                this.map.fitBounds(markersGroup.getBounds(), {padding: [50, 50]});
            } else {
                this.map.setView([data.orders[0].lat, data.orders[0].lng], 14);
            }

            setTimeout(() => {
                this.map.invalidateSize();
            }, 200);
        } catch (error) {
            console.error("FSM Map Loading Error:", error);
            canvas.innerHTML =
                '<div class="p-4 text-center text-danger">Erreur lors du traitement de la carte.</div>';
        }
    },
});

export default publicWidget.registry.FsmPortalMapSwitcher;
