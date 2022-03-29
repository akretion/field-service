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

    @api.constrains("is_abstract", "edit_type", "fsm_abstract_frequency_ids")
    def _check_quick_edit(self):
        for rec in self:
            if not rec.is_abstract or rec.edit_type != "quick_edit":
                continue
            invalid_frequencies = rec.fsm_abstract_frequency_ids.filtered(
                lambda f: not f.is_quick_editable
            )
            if invalid_frequencies:
                raise models.ValidationError(
                    _("The following frequencies are not weekly frequencies: %s")
                    % (", ".join(invalid_frequencies.mapped("name")))
                )
