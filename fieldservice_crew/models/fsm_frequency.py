# Copyright (C) 2021 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FSMFrequency(models.Model):
    _inherit = "fsm.frequency"

    fsm_crew_member_ids = fields.One2many(
        comodel_name="fsm.recurring.order.member",
        inverse_name="fsm_frequency_rule_id",
    )

    fsm_worker_ids = fields.Many2many(
        comodel_name="fsm.person",
        inverse="_inverse_fsm_worker_ids",
        compute="_compute_fsm_worker_ids",
    )

    def _compute_fsm_worker_ids(self):
        for rec in self:
            rec.fsm_worker_ids = rec.fsm_crew_member_ids.mapped("fsm_worker_id")

    def _inverse_fsm_worker_ids(self):
        if not self.fsm_recurring_id:
            return
        to_remove = self.fsm_crew_member_ids.filtered(
            lambda crew: crew.fsm_worker_id.id not in self.fsm_worker_ids.ids
        )
        to_add = self.fsm_worker_ids - self.fsm_crew_member_ids.mapped("fsm_worker_id")
        self.fsm_crew_member_ids.create(
            [
                {
                    "fsm_worker_id": fsm_worker.id,
                    "fsm_frequency_rule_id": self.id,
                    "fsm_recurring_id": self.fsm_recurring_id.id,
                }
                for fsm_worker in to_add
            ]
        )
        to_remove.unlink()
