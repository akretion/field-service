# Copyright (C) 2019 - TODAY, mourad EL HADJ MIMOUNE, Akretion
# Copyright (C) 2021 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class FSMRecurringOrder(models.Model):
    _inherit = "fsm.recurring"

    is_fsm_frequency_set_abstract = fields.Boolean()
    fsm_abstract_frequency_set_id = fields.Many2one(
        "fsm.frequency.set",
        "Generic Frequency Set",
        index=True,
        copy=True,
        help="Frequency of the service",
        domain=[("is_abstract", "=", True)],
    )
    fsm_concrete_frequency_set_id = fields.Many2one(
        "fsm.frequency.set",
        "Concrete Frequency",
        copy=False,
    )
    # The two following fields are technical one to be used in the form view edition
    # We need these two to be able to edit the frequency set diffrently in the form view
    fsm_quick_edit_concrete_frequency_ids = fields.Many2many(
        "fsm.frequency",
        compute="_compute_fsm_quick_edit_concrete_frequency_ids",
        inverse="_inverse_fsm_quick_edit_concrete_frequency_ids",
    )
    fsm_advanced_concrete_frequency_ids = fields.Many2many(
        "fsm.frequency",
        compute="_compute_fsm_advanced_concrete_frequency_ids",
        inverse="_inverse_fsm_advanced_concrete_frequency_ids",
    )

    fsm_frequency_set_id = fields.Many2one(related="fsm_concrete_frequency_set_id")

    fsm_frequency_ids = fields.Many2many(
        related="fsm_concrete_frequency_set_id.fsm_frequency_ids"
    )

    edit_type = fields.Selection(related="fsm_concrete_frequency_set_id.edit_type")

    @api.depends("fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids")
    def _compute_fsm_quick_edit_concrete_frequency_ids(self):
        for rec in self:
            rec.fsm_quick_edit_concrete_frequency_ids = (
                rec.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids
            )

    def _inverse_fsm_quick_edit_concrete_frequency_ids(self):
        for rec in self:
            rec.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids = (
                rec.fsm_quick_edit_concrete_frequency_ids
            )

    @api.depends("fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids")
    def _compute_fsm_advanced_concrete_frequency_ids(self):
        for rec in self:
            rec.fsm_advanced_concrete_frequency_ids = (
                rec.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids
            )

    def _inverse_fsm_advanced_concrete_frequency_ids(self):
        for rec in self:
            rec.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids = (
                rec.fsm_advanced_concrete_frequency_ids
            )

    @api.model
    def create(self, values):
        recurring = super().create(values)
        if not recurring.fsm_concrete_frequency_set_id:
            # always create a fsm_concrete for each recurring.
            # it's a bit overkill but spare us lots of issues.
            concrete_freq_set_id = self.env["fsm.frequency.set"].create(
                {
                    "name": recurring.name,
                    "is_abstract": False,
                }
            )
            recurring.fsm_concrete_frequency_set_id = concrete_freq_set_id
            if recurring.fsm_abstract_frequency_set_id:
                recurring.fsm_concrete_frequency_set_id.edit_type = (
                    recurring.fsm_abstract_frequency_set_id.edit_type
                )

            # Also copy abstract frequencies in concrete frequency set
            for freq in recurring.fsm_abstract_frequency_set_id.fsm_frequency_ids:
                new_freq = freq.copy(
                    {
                        "origin": recurring.fsm_abstract_frequency_set_id.name,
                        "is_abstract": False,
                        "fsm_recurring_id": recurring.id,
                    }
                )
                self.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids |= (
                    new_freq
                )
        return recurring

    def write(self, values):
        old_abstract = {rec: rec.fsm_abstract_frequency_set_id.id for rec in self}
        result = super().write(values)
        for rec in self:
            if (
                rec.fsm_abstract_frequency_set_id
                and rec.fsm_abstract_frequency_set_id.id != old_abstract[rec]
            ):
                # Set the abstract frequency schedule days to the concrete one
                # only if the abstract was changed
                rec.fsm_concrete_frequency_set_id.schedule_days = (
                    rec.fsm_abstract_frequency_set_id.schedule_days
                )

        return result

    def action_convert_to_advanced(self):
        self.fsm_concrete_frequency_set_id.edit_type = "advanced"

    def action_convert_to_weekly(self):
        self.fsm_concrete_frequency_set_id.edit_type = "quick_edit"
        self.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids.filtered(
            lambda x: not x.is_quick_editable
        ).unlink()

    def action_restore_abstract_frequencies(self):
        if self.fsm_abstract_frequency_set_id:
            self.fsm_concrete_frequency_set_id.edit_type = (
                self.fsm_abstract_frequency_set_id.edit_type
            )
            self.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids.unlink()

            # Also copy abstract frequencies in concrete frequency set
            for freq in self.fsm_abstract_frequency_set_id.fsm_frequency_ids:
                new_freq = freq.copy(
                    {
                        "origin": self.fsm_abstract_frequency_set_id.name,
                        "is_abstract": False,
                        "fsm_recurring_id": self.id,
                    }
                )
                self.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids |= (
                    new_freq
                )

    def action_view_fms_order(self):
        # TODO: move this in parent
        fms_orders = self.mapped("fsm_order_ids")
        action = self.env.ref("fieldservice.action_fsm_operation_order").read()[0]
        if len(fms_orders) > 1:
            action["domain"] = [("id", "in", fms_orders.ids)]
        elif len(fms_orders) == 1:
            form_view = [(self.env.ref("fieldservice.fsm_order_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = fms_orders.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        action["key2"] = "client_action_multi"
        return action

    def generate_orders(self):
        """
        Executed from form view (call private method) _generate_orders
        """
        return self._generate_orders()
