# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	origin_type = fields.Selection([
		('amadeus', 'Ticketing'),
		('to', 'Tour Operator')
	], string="Order Origin Type")

	# @api.model
	# def create(self, vals):
	# 	if 'order_ref' in vals:
	# 		order = self.env['travel.order'].search([('ref', '=', vals['order_ref'])])
	# 		if order and order.document_type != vals['origin_type']:
	# 			raise UserError(_(
	# 				"The selected invoice origine type does not match with the order type\n"\
	# 				"Selected invoice origine type : %s\n"\
	# 				"Order (%s) with reference %s type : %s" % (vals['origin_type'], order.name, vals['order_ref'], order.document_type)
	# 			))

	# @api.onchange('origin_type')
	# def onchange_origin_type(self):
	# 	if self.order_ref:
	# 		order = self.env['travel.order'].search([('ref', '=', self.order_ref)])
	# 		if not order:
	# 			raise UserError(_("Order Reference %s not found!") % self.order_ref)
	# 		elif order.document_type != self.origin_type:
	# 			raise UserError(_(
	# 				"The selected invoice origine type does not match with the order type\n"\
	# 				"Selected invoice origine type : %s\n"\
	# 				"Order (%s) with reference %s type : %s" % (self.origin_type, order.name, self.order_ref, order.document_type)
	# 			))