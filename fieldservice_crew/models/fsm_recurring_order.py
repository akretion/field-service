# Copyright (C) 2021 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FSMRecurringOrder(models.Model):
    _inherit = "fsm.recurring"

    crew_member_ids = fields.One2many(
        "fsm.recurring.order.member",
        'fsm_recurring_id',
        string="Recurring Members",
    )

    crew_total_duration = fields.Float(
        compute="_calc_crew_total_duration")

    @api.depends("crew_member_ids.scheduled_duration")
    def _calc_crew_total_duration(self):
        for rec in self:
            rec.crew_total_duration = sum(rec.crew_member_ids.mapped('scheduled_duration'))

    def _create_order(self, date=None):
        self.ensure_one()
        order = super()._create_order(date)
        new_crew = self._generate_crew(order)
        order.crew_member_ids = [(6, False, new_crew.ids)]
        return order

    def _generate_crew(self, order):
        lines = []
        for crew_member_tmpl in self.crew_member_ids:
            if crew_member_tmpl._is_active_on_date(order.scheduled_date_start, order.scheduled_date_end):
                lines.append(crew_member_tmpl._prepare_crew_values(order))
        return self.env["fsm.order.member"].create(lines)


class FSMRecurringCrewMember(models.Model):
    _name = "fsm.recurring.order.member"
    _description = 'FSM Recurring Order Member'
    _order = 'fsm_recurring_id, sequence, id'

    _sql_constraints = [
        ("name_uniq", "unique (fsmwork_recurring_id,fsm_frequency_rule_id,  )", "Vehicle name already exists!"),
    ]

    sequence = fields.Integer(string='Sequence', default=10)
    fsm_recurring_id = fields.Many2one('fsm.recurring',
        string='Recurring Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    scheduled_duration = fields.Float(
        string="Scheduled duration", help="Scheduled duration of the work in hours"
    )
    fsm_frequency_rule_id = fields.Many2one(
        "fsm.frequency", "Frequency Rule",
    )
    worker_id = fields.Many2one("fsm.person", string="Worker", index=True)

    def _is_active_on_date(self, date_start, date_end):
        if self.fsm_frequency_rule_id:
            return self._freq_is_active_on_date(date_start, date_end)
        on_calendar = self._calendar_is_active_on_date(date_start, date_end)
        return on_calendar

    def _calendar_is_active_on_date(self, date_start, date_end):
        calendar = self.worker_id.resource_calendar_id
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

    def _prepare_crew_values(self, order):
        return {
            "fsm_order_id": order.id,
            "scheduled_date_start": order.scheduled_date_start,
            "scheduled_duration": self.scheduled_duration,
            "worker_id": self.worker_id.id,
        }
