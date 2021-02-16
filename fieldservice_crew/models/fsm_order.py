# Copyright (C) 2021 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    crew_member_ids = fields.One2many(
        "fsm.order.member",
        "fsm_order_id",
        string="Members",
    )

    crew_total_duration = fields.Float(compute="_calc_crew_total_duration")

    @api.depends("crew_member_ids.scheduled_duration")
    def _calc_crew_total_duration(self):
        for rec in self:
            rec.crew_total_duration = sum(
                rec.crew_member_ids.mapped("scheduled_duration")
            )

    # TODO: replace assign_to by the first of the crew


class FSMCrewMember(models.Model):
    _name = "fsm.order.member"
    _description = "FSM Order Member"
    _order = "fsm_order_id, sequence, id"
    _sql_constraints = [
        (
            "fsm_order_member_unicity",
            "unique (fsm_order_id, worker_id)",
            "Worker already on order",
        ),
    ]

    sequence = fields.Integer(string="Sequence", default=10)
    fsm_order_id = fields.Many2one(
        "fsm.order",
        string="Order Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    scheduled_date_start = fields.Datetime(string="Scheduled Start (ETA)")
    scheduled_duration = fields.Float(
        string="Scheduled duration", help="Scheduled duration of the work in" " hours"
    )
    scheduled_date_end = fields.Datetime(string="Scheduled End")

    worker_id = fields.Many2one("fsm.person", string="Worker", index=True)

    @api.onchange("fsm_order_id")
    def _onchange_fsm_order_id(self):
        for rec in self:
            rec.scheduled_date_start = rec.fsm_order_id.scheduled_date_start
            rec.scheduled_duration = rec.fsm_order_id.scheduled_duration
