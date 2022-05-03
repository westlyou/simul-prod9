# -*- coding: utf-8 -*-

from odoo import _
from odoo.exceptions import UserError
from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter

from datetime import datetime as dt
from datetime import timedelta as td

class StateExcelReportController(http.Controller):
	@http.route([
		'/state/excel_report/<model("account.extractions.wizard"):wizard>',
	], type='http', auth='user', csrf=False)
	def get_state_excel_report(self, wizard=None, **args):
		# The izard parameter is the primary key that odoo sent
		# with the get_excel_report method in the ng.sale.log.wizard model
		# contains partners, start date and end date

		# create a response with a header in the form of an excel file
		# so the browser will immediately download it
		# The Content-Disposition header is the fiel name fill as needed

		response = request.make_response(
			None,
			headers=[
				('Content-Type', 'application/vnd.ms-excel'),
				('content-Disposition', content_disposition(_('State.xlsx')))
			]
		)

		# create workbook object from xlsxwriter library
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {'in_memory' : True})

		# create some style to set up the font type, the font size, the border and the alignment
		title_style = workbook.add_format({'font_name' : 'Calibri', 'font_size' : 14, 'bold' : True, 'align' : 'center', 'valign' : 'middle'})
		header_style = workbook.add_format({'font_name' : 'Calibri', 'bold' : True, 'bottom' : 1, 'align' : 'center', 'valign' : 'middle', 'text_wrap' : 1})
		text_style = workbook.add_format({'font_name' : 'Calibri', 'align' : 'left', 'valign' : 'middle', 'text_wrap' : 1})
		number_style = workbook.add_format({'font_name' : 'Calibri', 'align' : 'right', 'valign' : 'middle', 'num_format' : '#,##0'})
		footer_style = workbook.add_format({'font_name' : 'Calibri', 'top' : 1, 'bold' : True, 'align' : 'center'})
		sum_style = workbook.add_format({'font_name' : 'Calibri', 'top' : 1, 'bold' : True, 'align' : 'right', 'num_format' : '#,##0'})

		# loop for all partners
		for partner in wizard.partner_ids:
			# create worksheet/tab per partner
			sheet = workbook.add_worksheet(partner.name)
			# set the orientation to landscape
			sheet.set_landscape()
			# set up the paper size, 9 means A4
			sheet.set_paper(9)
			# set up the margin in inch
			sheet.set_margins(0.5,0.5,0.5,0.5)

			# set up the column width
			sheet.set_column('A:B', 10)
			sheet.set_column('C:E', 30)
			sheet.set_column('F:G', 20)
			sheet.set_column('H:J', 14)
			sheet.set_column('K:K', 15)

			# the report title
			# merge the A1 to E1 cell and apply the style font size : 14, font weight bold
			sheet.merge_range('A1:K1', _('S.I.G.M. State (%s)' % partner.name), title_style)

			# table title
			sheet.write(1, 0, _('Number'), header_style)
			sheet.write(1, 1, _('Date'), header_style)
			sheet.write(1, 2, _('Company'), header_style)
			sheet.write(1, 3, _('Description'), header_style)
			sheet.write(1, 4, _('Passenger'), header_style)
			sheet.write(1, 5, _('Ticket Number'), header_style)
			sheet.write(1, 6, _('Journey'), header_style)
			sheet.write(1, 7, _('Transport'), header_style)
			sheet.write(1, 8, _('Other Tax'), header_style)
			sheet.write(1, 9, _('VAT'), header_style)
			sheet.write(1, 10, _('Total'), header_style)

			row = 2
			number = 1

			# search the sales order
			# invoices = request.env['account.move'].search([('partner_id', '=', partner.id), ('invoice_date', '>=', wizard.start_date), ('invoice_date', '<=', wizard.end_date)], order="invoice_date")
			# invoices = request.env['account.move'].search([('invoice_date', '=', date)])
			start_date_filter = ('invoice_date', '>=', wizard.start_date) if wizard.start_date else (True, '=', True)
			end_date_filter = ('invoice_date', '<=', wizard.end_date) if wizard.end_date else (True, '=', True)
			origin_filter = ('origin_type', '=' if wizard.origin_type else 'in', wizard.origin_type if wizard.origin_type else ('to', 'amadeus'))

			# invoices = request.env['account.move'].search([('partner_id', '=', partner.id), start_date_filter, end_date_filter, origin_filter], order='invoice_date')
			# invoices = request.env['account.move.line'].search([
			invoice_lines = request.env['account.move.line'].search([
				('supplier', '=', partner.id), 
				('move_id', 'in', request.env['account.move'].search([origin_filter, start_date_filter, end_date_filter]).ids)
			], order='date')

			# for invoice in invoices:
			# for invoice in invoice_lines:
			for line in invoice_lines:
				# the report content
				# for line in invoice.invoice_line_ids:
				force_sign = -1 if 'refund' in line.move_id.move_type else 1
				
				sheet.write(row, 0, line.move_id.name, text_style)
				sheet.write(row, 1, dt.strftime(line.move_id.invoice_date, '%d/%m/%Y'), text_style)
				sheet.write(row, 2, line.move_id.partner_id.name, text_style)
				sheet.write(row, 3, line.name, text_style)
				sheet.write(row, 4, line.passenger if line.passenger else '', text_style)
				sheet.write(row, 5, line.ticket_number if line.ticket_number else '', text_style)
				sheet.write(row, 6, line.journey if line.journey else '', text_style)
				sheet.write(row, 7, force_sign * line.price_unit, number_style)
				sheet.write(row, 8, force_sign * line.other_tax, number_style)
				sheet.write(row, 9, force_sign * line.amount_tva, number_style)
				sheet.write(row, 10, force_sign * line.price_total, number_style)

				row += 1
				number += 1

			# create a formula to sum the total sales
			sheet.merge_range('A' + str(row+1) + ':G' + str(row+1), 'Total', footer_style)
			sheet.write_formula(row, 7, '=SUM(H3:H' + str(row) + ')', sum_style)
			sheet.write_formula(row, 8, '=SUM(I3:I' + str(row) + ')', sum_style)
			sheet.write_formula(row, 9, '=SUM(J3:J' + str(row) + ')', sum_style)
			sheet.write_formula(row, 10, '=SUM(K3:K' + str(row) + ')', sum_style)

		# return the excel file as a response, so the browser can download it
		workbook.close()
		output.seek(0)
		response.stream.write(output.read())
		output.close()

		return response

	# @http.route('/web/print', type='http', auth='user')
	# def print_sales_log(self, wizard=None, **args):

	# 	response = request.make_response(
	# 		None,
	# 		headers=[
	# 			('Content-Type', 'application/vnd.ms-excel'),
	# 			('content-Disposition', content_disposition(_('Saleslog.pdf')))
	# 		]
	# 	)

	# 	return response