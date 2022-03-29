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
    fsm_frequency_qedit_ids = fields.One2many(
        "fsm.frequency",
        "fsm_recurring_id",
        copy=False,
        domain="[('is_quick_editable','=', True)]",
        compute="_compute_quickedit",
        inverse="_inverse_quickedit",
        store=True,
        help="Technical field used to allow a quick edit of fsm_frequency_ids",
    )
    fsm_concrete_frequency_ids = fields.Many2many(
        # do not work if related
        "fsm.frequency",
        compute="_compute_fsm_concrete_frequency_ids",
        inverse="_inverse_fsm_concrete_frequency_ids",
    )
    fsm_frequency_ids = fields.Many2many(
        related="fsm_frequency_set_id.fsm_frequency_ids"
    )

    fsm_concrete_frequency_set_id = fields.Many2one(
        "fsm.frequency.set",
        "Concrete Frequency",
        copy=False,
    )

    fsm_frequency_set_id = fields.Many2one(
        compute="_compute_fsm_frequency_set_id", readonly=True, store=True
    )

    edit_type = fields.Selection(
        [("quick_edit", "Weekly"), ("advanced", "Advanced"), ("none", "")],
        default="none",
    )

    @api.depends("fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids")
    def _compute_fsm_concrete_frequency_ids(self):
        for rec in self:
            rec.fsm_concrete_frequency_ids = (
                rec.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids
            )

    def _inverse_fsm_concrete_frequency_ids(self):
        for rec in self:
            rec.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids = (
                rec.fsm_concrete_frequency_ids
            )

    @api.depends("edit_type", "fsm_abstract_frequency_set_id")
    def _compute_fsm_frequency_set_id(self):
        for rec in self:
            if rec.edit_type == "none":
                rec.fsm_frequency_set_id = rec.fsm_abstract_frequency_set_id
            else:
                # TODO copy frequency_set params like buffer, days ahead ?
                rec.fsm_frequency_set_id = rec.fsm_concrete_frequency_set_id

    @api.depends("edit_type", "fsm_abstract_frequency_set_id")
    def _compute_quickedit(self):
        for rec in self:
            if not rec.fsm_concrete_frequency_set_id:
                # save first
                continue

            if rec.edit_type == "quick_edit" and rec.fsm_abstract_frequency_set_id:
                if (
                    not len(
                        rec.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids
                    )
                    == 0
                ):
                    # we do not know if old value was advanced or none
                    # always copy concrete freq
                    # if one wants to restart from blank
                    # just delete all the concrete lines
                    rec.fsm_frequency_qedit_ids = (
                        rec.fsm_concrete_frequency_set_id.fsm_concrete_frequency_ids
                    )

    def _inverse_quickedit(self):
        for rec in self:
            if rec.fsm_frequency_qedit_ids:
                to_rm = rec.fsm_concrete_frequency_ids - rec.fsm_frequency_qedit_ids
                to_rm.unlink()
                rec.fsm_concrete_frequency_ids = rec.fsm_frequency_qedit_ids

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
                recurring.edit_type = recurring.fsm_abstract_frequency_set_id.edit_type

            # Also copy abstract frequencies in concrete frequency set
            for freq in recurring.fsm_abstract_frequency_set_id.fsm_frequency_ids:
                new_freq = freq.copy(
                    {
                        "origin": recurring.fsm_abstract_frequency_set_id.name,
                        "is_abstract": False,
                        "fsm_recurring_id": recurring.id,
                    }
                )
                recurring.fsm_frequency_qedit_ids |= new_freq
                recurring.fsm_concrete_frequency_ids |= new_freq
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
                # Should we reset frequencies?

            # kind of inverse method for related fields
            # new frequencies may exist here but not linked to
            # frequency_set
            # and unlinked frequency can be there too
            freq_set = rec.fsm_concrete_frequency_set_id
            if rec.edit_type == "quick_edit":
                frequencies = rec.fsm_frequency_qedit_ids
            elif rec.edit_type == "advanced":
                frequencies = rec.fsm_frequency_ids.filtered(
                    lambda x: not x.is_abstract
                )
                to_rm = rec.fsm_concrete_frequency_ids - frequencies
                to_rm.unlink()
            else:
                continue
            freq_set.fsm_concrete_frequency_ids = [(6, 0, frequencies.ids)]
        return result

    def action_convert_to_advanced(self):
        self.edit_type = "advanced"

    def action_convert_to_weekly(self):
        self.edit_type = "quick_edit"
        self.fsm_concrete_frequency_ids.filtered(
            lambda x: not x.is_quick_editable
        ).unlink()

    def action_restore_abstract_frequencies(self):
        if self.fsm_abstract_frequency_set_id:
            self.edit_type = self.fsm_abstract_frequency_set_id.edit_type
            self.fsm_concrete_frequency_ids.unlink()

            # Also copy abstract frequencies in concrete frequency set
            for freq in self.fsm_abstract_frequency_set_id.fsm_frequency_ids:
                new_freq = freq.copy(
                    {
                        "origin": self.fsm_abstract_frequency_set_id.name,
                        "is_abstract": False,
                        "fsm_recurring_id": self.id,
                    }
                )
                self.fsm_frequency_qedit_ids |= new_freq
                self.fsm_concrete_frequency_ids |= new_freq

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
