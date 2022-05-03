# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime as dt

class AccountExtractionsWizard(models.TransientModel):
	_name = 'account.extractions.wizard'
	_description = 'Account Extractions'

	partner_ids = fields.Many2many('res.partner', string="Companies")
	start_date = fields.Date("Start Date")
	end_date = fields.Date("End Date")
	origin_type = fields.Selection([
		('amadeus', 'Billeterie'),
		('to', 'Tour Operator')
	], string="Origin Type")

	def get_excel_report(self):
		# redirect to /salelog/excel_report controller to generate the excel file
		return {
			'type' : 'ir.actions.act_url',
			'url' : '/state/excel_report/%s' %(self.id),
			'target' : 'new'
		}

	def print_sales_log(self):
		origin_filter = ('origin_type', '=' if self.origin_type else 'in', self.origin_type if self.origin_type else ('to', 'amadeus'))
		invoices = self.env['account.move'].search([
			('invoice_date', '>=', self.start_date), 
			('invoice_date', '<=', self.end_date), 
			('move_type', 'in', ('out_invoice', 'out_refund')),
			('state', '=', 'posted'),
			origin_filter
		], order="name, invoice_date")
		return self.env.ref('account_extractions.action_print_sales_log').report_action(invoices)
