# Copyright (C) 2022 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    fsm_order_ids = fields.Many2many(
        "fsm.order", relation="fsm_order_roster", readonly=True
    )
    fsm_recurring_order_ids = fields.Many2many(
        "fsm.recurring", relation="fsm_recurring_order_roster", readonly=True
    )
    fsm_order_count = fields.Integer(
        compute="_compute_fsm_order_count", string="FSM Orders"
    )
    fsm_recurring_count = fields.Integer(
        compute="_compute_fsm_recurring_count", string="FSM Recurring"
    )

    def _compute_fsm_order_count(self):
        for employee in self:
            employee.fsm_order_count = len(employee.fsm_order_ids)

    def _compute_fsm_recurring_count(self):
        for employee in self:
            employee.fsm_recurring_count = len(employee.fsm_recurring_order_ids)

    def action_view_fsm_order(self):
        self.ensure_one()
        fsm_orders = self.mapped("fsm_order_ids")
        action = self.env.ref("fieldservice.action_fsm_dash_order").read()[0]
        if len(fsm_orders) > 1:
            action["domain"] = [("id", "in", fsm_orders.ids)]
            action["views"] = [
                (False, "tree"),
                (False, "form"),
                (False, "calendar"),
                (False, "kanban"),
            ]
        elif len(fsm_orders) == 1:
            action["views"] = [
                (
                    self.env.ref("fieldservice.fsm_order_form").id,
                    "form",
                )
            ]
            action["res_id"] = fsm_orders.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def action_view_fsm_recurring(self):
        self.ensure_one()
        fsm_recurrings = self.mapped("fsm_recurring_order_ids")
        action = self.env.ref("fieldservice_recurring.action_fsm_recurring").read()[0]
        if len(fsm_recurrings) > 1:
            action["domain"] = [("id", "in", fsm_recurrings.ids)]
        elif len(fsm_recurrings) == 1:
            action["views"] = [
                (
                    self.env.ref("fieldservice_recurring.fsm_recurring_form_view").id,
                    "form",
                )
            ]
            action["res_id"] = fsm_recurrings.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action
