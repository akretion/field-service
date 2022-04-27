# Copyright (C) 2019 - TODAY, mourad EL HADJ MIMOUNE, Akretion
# Copyright (C) 2021 - raphael.reverdy@akretion.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Field Service Recurring Quick edit",
    "summary": "Add frequency quick edition on recurring order",
    "version": "14.0.1.0.0",
    "category": "Field Service",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/field-service",
    "depends": [
        "contract",
        "fieldservice_recurring", "fieldservice_sale_frequency"],
    "data": ["views/fsm_frequency.xml", "views/fsm_recurring.xml",],
    "license": "AGPL-3",
    "installable": True,
}
