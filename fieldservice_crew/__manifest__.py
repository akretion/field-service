# Copyright (C) 2021 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Field Service Crew",
    "summary": "Multiple workers per orders",
    "version": "14.0.1.1.0",
    "license": "AGPL-3",
    "category": "Field Service",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/field-service",
    "depends": [
        "fieldservice",
        "fieldservice_recurring",
        "fieldservice_recurring_quick_edit",
        "resource",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/fsm_order.xml",
        "views/fsm_recurring_order.xml",
    ],
    "demo": [
    ],
    "application": True,
    "development_status": "Beta",
    "maintainers": ["hparfr"],
}
