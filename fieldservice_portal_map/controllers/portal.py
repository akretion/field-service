import logging

from odoo import http
from odoo.http import request
from odoo.osv.expression import OR

from odoo.addons.fieldservice_portal.controllers.fsm_order_portal import CustomerPortal

_logger = logging.getLogger(__name__)


class FsmCustomerPortalMap(CustomerPortal):
    @http.route(["/my/fsm_orders/map_data"], type="json", auth="user", website=True)
    def get_fsm_orders_map_data(
        self, search=None, search_in="all", filterby=None, **kw
    ):
        """Fetches geographical data of interventions for the Leaflet display"""
        FsmOrder = request.env["fsm.order"]

        try:
            # Step 1: Strict retrieval of the native portal security domain (Filtered by customer)
            domain = self._prepare_fsm_orders_domain()
        except Exception:
            # Secure fallback if the parent method requires contextual arguments
            domain = [
                (
                    "partner_id",
                    "=",
                    request.env.user.partner_id.commercial_partner_id.id,
                )
            ]

        # Application of text search bar filters
        if search and search_in:
            searchbar_inputs = {
                "all": "all",
                "name": "name",
                "description": "description",
                "location_id.name": "location",
            }
            search_domain = []
            for search_property, input_val in searchbar_inputs.items():
                if search_in == input_val or search_in == "all":
                    if search_property != "all":
                        search_domain = OR(
                            [search_domain, [(search_property, "ilike", search)]]
                        )
            domain += search_domain

        # Application of stage filters (Open / Closed)
        if filterby and filterby != "all":
            if filterby == "open":
                domain += [("is_closed", "=", False)]
            else:
                domain += [("stage_id.name", "=", filterby)]
        elif not filterby:
            domain += [("is_closed", "=", False)]

        # Step 2: Search for orders with the user's permissions (Security preserved)
        orders = FsmOrder.search(domain)

        features = []
        for order in orders:
            # Step 3: ACL SECURITY FIXED
            # We switch the record to `.sudo()` ONLY to read the location coordinates
            # without the Odoo engine raising an Access Denied error for the portal user.
            sudo_order = order.sudo()
            loc = sudo_order.location_id

            if not loc:
                continue

            lat = loc.partner_latitude
            lng = loc.partner_longitude

            # If coordinates do not exist or are equal to 0, ignore the element
            if not lat or not lng or lat == 0 or lng == 0:
                _logger.warning(
                    "FSM intervention %s (Location: %s) does not have valid GPS coordinates.",
                    order.name,
                    loc.name,
                )
                continue

            features.append(
                {
                    "id": order.id,
                    "name": order.name,
                    "lat": lat,
                    "lng": lng,
                    "stage": order.stage_id.name if order.stage_id else "N/A",
                    "location": loc.display_name or "",
                    "type": order.type.name if order.type else "",
                    "desc": order.description or "",
                }
            )

        return {"orders": features}
