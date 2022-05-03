# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	customer_name = fields.Char(string="Customer Name")
	customer_address = fields.Char(string="Address")
	customer_type = fields.Selection([
		('account', 'Customer account'),
		('passing', 'Passing customer')
	], string="Customer Type", compute="_get_customer_type")

	@api.depends('partner_id.customer_type')
	def _get_customer_type(self):
		for record in self:
			record.customer_type = record.partner_id.customer_type