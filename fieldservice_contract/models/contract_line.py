# Copyright 2019 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class ContractLine(models.Model):
    _inherit = 'contract.line'

    fsm_recurring_id = fields.Many2one(
        'fsm.recurring', 'FSM Recurring Order', index=True, readonly=True,
        help="Field Service Recurring Order generated by the sale order line")

    fsm_direct_order_id = fields.Many2one(
        'fsm.order', 'FSM Order', index=True, readonly=True,
        # only direct orders, not the ones generated by recurring order
        help="Field Service Order generated by the contract line")

    fsm_order_ids = fields.One2many(
        comodel_name='fsm.order',
        inverse_name='contract_line_id',
        string='FSM Orders', index=True,
        readonly=True, copy=False,
        help="All FSM Orders linked to this contract line",
        # recurring and direct orders
    )

    @api.multi
    def _prepare_invoice_line(self, invoice_id):
        # add link fsm orders to invoice line
        res = super(ContractLine, self)._prepare_invoice_line(
            invoice_id
        )
        dates = self._get_period_to_invoice(
            self.last_date_invoiced, self.recurring_next_date
        )
        fsm_orders = self._invoiceable_fsm_order(*dates)
        if fsm_orders:
            res.update({'fsm_order_ids': [(6, 0, fsm_orders.ids)]})
        return res

    @api.multi
    def _get_quantity_to_invoice(
        self, period_first_date, period_last_date, invoice_date
    ):
        # here we do not have link yet between invoice.line
        # and fsm orders
        self.ensure_one()
        quantity = 0
        if self.fsm_direct_order_id or self.fsm_recurring_id:
            quantity = len(self._invoiceable_fsm_order(
                period_first_date,
                period_last_date,
                invoice_date))
        else:
            quantity = super()._get_quantity_to_invoice(
                period_first_date,
                period_last_date,
                invoice_date)
        return quantity

    @api.multi
    def _invoiceable_fsm_order(
        self, period_first_date, period_last_date, invoice_date
    ):
        dom = [
            ('scheduled_date_start', '>=', period_first_date),
            ('scheduled_date_start', '<=', period_last_date),
            ('contract_line_id', '=', self.id),
            ('invoice_line_id', '=', False),
        ]
        return self.env['fsm.order'].search(dom)

    @api.model
    def create(self, values):
        line = super().create(values)
        prod = line.product_id
        if (
            prod.fsm_recurring_template_id or
            prod.fsm_order_template_id
        ):
            line._field_service_generation()
        return line

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if 'date_start' in vals or 'date_end' in vals:
            self.update_fsm_date(vals)
        return res

    @api.multi
    def update_fsm_date(self, vals):
        to_apply = {}
        if 'date_start' in vals:
            to_apply['start_date'] = vals['date_start']
        if 'date_end' in vals:
            to_apply['end_date'] = vals['date_end']
        self.mapped('fsm_recurring_id').write(to_apply)

    def _fsm_create_fsm_common_prepare_values(self):
        return {
            'customer_id': self.contract_id.partner_id.id,
            'location_id': self.contract_id.fsm_location_id.id,
            'description': self.name,
            'contract_line_id': self.id,
            'company_id': self.contract_id.company_id.id,
        }

    def _field_create_fsm_order_prepare_values(self):
        self.ensure_one()
        res = self._fsm_create_fsm_common_prepare_values()
        res['scheduled_date_start'] = self.date_start
        res['template_id'] = self.product_id.fsm_order_template_id.id
        return res

    def _field_create_fsm_recurring_prepare_values(self):
        self.ensure_one()
        template = self.product_id.fsm_recurring_template_id
        note = self.name
        if template.description:
            note += '\n ' + template.description
        res = self._fsm_create_fsm_common_prepare_values()
        res['start_date'] = self.date_start
        res['end_date'] = self.date_end
        res['fsm_recurring_template_id'] = template.id
        res['description'] = note
        res['max_orders'] = template.max_orders
        res['fsm_frequency_set_id'] = template.fsm_frequency_set_id.id
        res['fsm_order_template_id'] = template.fsm_order_template_id.id
        return res

    @api.multi
    def _field_create_fsm_order(self):
        """ Generate fsm_order for the given line, and link it.
            :return a mapping with the line id and its linked fsm_order
            :rtype dict
        """
        result = {}
        for line in self:
            # create fsm_order
            values = line._field_create_fsm_order_prepare_values()
            fsm_order = self.env['fsm.order'].sudo().create(values)
            line.write({'fsm_direct_order_id': fsm_order.id})
            result[line.id] = fsm_order
        return result

    @api.multi
    def _field_create_fsm_recurring(self):
        """ Generate fsm_recurring for the given line, and link it.
            :return a mapping with the line id and its linked fsm_recurring
            :rtype dict
        """
        result = {}
        for line in self:
            # create fsm_recurring
            values = line._field_create_fsm_recurring_prepare_values()
            fsm_recurring = self.env['fsm.recurring'].sudo().create(values)
            # fsm_recurring.action_start()  # do not start yet
            line.write({'fsm_recurring_id': fsm_recurring.id})
            result[line.id] = fsm_recurring
        return result

    @api.multi
    def _field_find_fsm_order(self):
        """ Find the fsm_order generated by the lines. If no fsm_order
            linked, it will be created automatically.
            :return a mapping with the line id and its linked fsm_order
            :rtype dict
        """
        # one search for all lines
        fsm_orders = self.env['fsm.order'].search([
            ('contract_line_id', 'in', self.ids)])
        fsm_order_cl_mapping = {
            fsm_order.contract_line_id.id: fsm_order for
            fsm_order in fsm_orders}
        result = {}
        for line in self:
            # If the contract was confirmed, cancelled,
            # set to draft then confirmed,
            # avoid creating a new fsm_order.
            fsm_order = fsm_order_cl_mapping.get(line.id)
            # If not found, create one fsm_order for the line
            if not fsm_order:
                fsm_order = line._field_create_fsm_order()[line.id]
            result[line.id] = fsm_order
        return result

    @api.multi
    def _field_find_fsm_recurring(self):
        """ Find the fsm_recurring generated by the lines. If no
            fsm_recurring linked, it will be created automatically.
            :return a mapping with the line id and its linked
            fsm_recurring
            :rtype dict
        """
        # one search for all lines
        fsm_recurrings = self.env['fsm.recurring'].search([
            ('contract_line_id', 'in', self.ids)])
        fsm_recurring_cl_mapping = {
            fsm_recurring.contract_line_id.id:
                fsm_recurring for fsm_recurring in fsm_recurrings}
        result = {}
        for line in self:
            # If the contract was confirmed, cancelled, set to draft then confirmed,
            # avoid creating a new fsm_recurring.
            fsm_recurring = fsm_recurring_cl_mapping.get(line.id)
            # If not found, create one fsm_recurring for the line
            if not fsm_recurring:
                fsm_recurring = line._field_create_fsm_recurring()[line.id]
            result[line.id] = fsm_recurring
        return result

    @api.multi
    def _field_service_generation(self):
        """ For service lines, create the field service order. If it already
            exists, it simply links the existing one to the line.
        """
        for line in self:
            # create order
            if line.product_id.field_service_tracking == 'order':
                line._field_find_fsm_order()
            # create recurring order
            elif line.product_id.field_service_tracking == 'recurring':
                line._field_find_fsm_recurring()
