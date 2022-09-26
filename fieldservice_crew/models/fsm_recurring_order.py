# Copyright (C) 2021 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from odoo import fields, models


class FSMRecurringOrder(models.Model):
    _inherit = "fsm.recurring"

    crew_member_ids = fields.One2many(
        "fsm.recurring.order.member",
        "fsm_recurring_id",
        string="Recurring Members",
    )
    active_crew_member_ids = fields.One2many(
        "fsm.recurring.order.member",
        compute="_compute_active_crew_member_ids",
        string="Active Recurring Members",
    )
    crew_worker_ids = fields.Many2many(
        "hr.employee",
        compute="_compute_crew_worker_ids",
    )

    def _prepare_order_values(self, date=None):
        vals = super()._prepare_order_values(date)
        vals["crew_member_ids"] = [
            (
                0,
                0,
                member_vals,
            )
            for member_vals in self._prepare_crew_members_values(
                vals["scheduled_date_start"],
                vals["scheduled_date_start"]
                + timedelta(hours=vals["scheduled_duration"]),
            )
        ]
        return vals

    def _prepare_crew_members_values(self, date_start, date_end):
        return [
            crew_member_tmpl._prepare_crew_values()
            for crew_member_tmpl in self.crew_member_ids
            if crew_member_tmpl._is_active_on_date(date_start, date_end)
        ]

    def _compute_crew_worker_ids(self):
        for rec in self:
            rec.crew_worker_ids = rec.crew_member_ids.mapped("fsm_worker_id")

    def _compute_active_crew_member_ids(self):
        for rec in self:
            # Only link crew members that have an active fsm_frequency_rule
            rec.active_crew_member_ids = rec.crew_member_ids.filtered(
                lambda member: member.fsm_frequency_rule_id in rec.fsm_frequency_ids
            )


class FSMRecurringCrewMember(models.Model):
    _name = "fsm.recurring.order.member"
    _description = "FSM Recurring Order Member"
    _order = "fsm_recurring_id, id"

    _sql_constraints = [
        (
            "member_unique",
            "unique (fsm_recurring_id, fsm_frequency_rule_id, fsm_worker_id)",
            "Only one worker per frequency",
        ),
    ]

    fsm_recurring_id = fields.Many2one(
        "fsm.recurring",
        string="Recurring Order Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )

    fsm_frequency_rule_id = fields.Many2one(
        "fsm.frequency",
        "Frequency Rule",
        ondelete="cascade",
    )

    fsm_worker_id = fields.Many2one("hr.employee", string="Worker", index=True)

    def _is_active_on_date(self, date_start, date_end):
        if self.fsm_frequency_rule_id:
            return self._freq_is_active_on_date(date_start, date_end)
        on_calendar = self._calendar_is_active_on_date(date_start, date_end)
        return on_calendar

    def _calendar_is_active_on_date(self, date_start, date_end):
        calendar = self.fsm_worker_id.calendar_id
        if not calendar:
            return True
        # todo: check global leaves in domain ?
        worked = calendar.get_work_duration_data(date_start, date_end, domain=[])
        if sum(worked.values()) == 0:
            # sum days and hours because we don't care
            # we just to test if > 0
            return False
        else:
            return True

    def _freq_is_active_on_date(self, date_start, date_end):
        rule = self.fsm_frequency_rule_id
        if not rule:
            return True
        return len(list(rule._get_rrule(dtstart=date_start, until=date_end))) > 0

    def _prepare_crew_values(self):
        return {
            "fsm_worker_id": self.fsm_worker_id.id,
        }
