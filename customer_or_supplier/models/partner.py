# -*- encoding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
	_inherit = 'res.partner'

	is_customer = fields.Boolean(string="Is Customer", compute="_compute_type")
	is_supplier = fields.Boolean(string="Is Supplier", compute="_compute_type")

	def _compute_type(self):
		for record in self:
			record.update({
				'is_customer' : not record.customer_rank == 0,
				'is_supplier' : not record.supplier_rank == 0,
			})