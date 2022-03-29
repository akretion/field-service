# Copyright (C) 2021 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.rrule import rruleset

from odoo import _, api, fields, models


class FSMFrequencySet(models.Model):
    _inherit = "fsm.frequency.set"

    fsm_concrete_recurring_id = fields.One2many(
        comodel_name="fsm.recurring",
        inverse_name="fsm_concrete_frequency_set_id",
        readonly=True,
    )

    fsm_concrete_frequency_ids = fields.Many2many(
        domain="[('is_abstract', '=', False), ('fsm_recurring_id','=', False)]",
    )

    edit_type = fields.Selection(
        [
            ("quick_edit", "Weekly"),
            ("advanced", "Advanced"),
        ],
        default="quick_edit",
    )
