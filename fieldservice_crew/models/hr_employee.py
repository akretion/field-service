# Copyright (C) 2022 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    fsm_order_ids = fields.Many2many(
        "fsm.order",
        relation="fsm_order_roster",
        readonly=True
    )
    fsm_recurring_order_ids = fields.Many2many(
        "fsm.recurring",
        relation="fsm_recurring_order_roster",
        readonly=True
    )

    def action_view_fsm_order(self):
        self.ensure_one()

        fsm_orders = self.mapped('fsm_order_ids')
        action = self.env.ref('fieldservice.action_fsm_dash_order').read()[0]
        if len(fsm_orders) == 1:
            action['views'] = [(self.env.ref('fieldservice.fsm_order_form').id,
                                'form')]
            action['res_id'] = fsm_orders.id
        else:
            # Display the FSM orders by searching for them
            action['context'] = "%s" % (
                {'search_default_fsm_worker_ids': self.id})
            # Display calendar first but change the displaying icons order
            action['views'] = [
                 (False, 'tree'),
                 (False, 'calendar'),
                 (False, 'kanban'),
            #     (False, 'timeline'), # timeline is not in the depencies
                 (False, 'form'),
            ]
        return action
