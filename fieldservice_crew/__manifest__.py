# Copyright (C) 2021 Akretion
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
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
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/fsm_order.xml",
        "views/fsm_recurring_order.xml",
        "views/fsm_frequency.xml",
        "views/hr_employee.xml",
        "views/assets.xml",
    ],
    "qweb": ["static/src/xml/*.xml"],
    "demo": [],
    "application": True,
    "development_status": "Beta",
    "maintainers": ["hparfr"],
}

# TODO:
# add Master Data > Crew
# add on a fsm.person form view a smart button
# to view fsm orders of the user
