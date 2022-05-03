# -*- coding: utf-8 -*-

from odoo import _
from odoo.exceptions import UserError
from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter

from datetime import datetime as dt

class SaleLogExcelReportController(http.Controller):
	@http.route([
		'/salelog/excel_report/<model("ng.sale.log.wizard"):wizard>',
	], type='http', auth='user', csrf=False)
	def get_salelog_excel_report(self, wizard=None, **args):
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
				('content-Disposition', content_disposition('Sales Log Report in Excel Format' + '.xlsx'))
			]
		)

		# create workbook object from xlsxwriter library
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {'in_memory' : True})

		# create some style to set up the font type, the font size, the border and the alignment
		title_style = workbook.add_format({'font_name' : 'Times', 'font_size' : 14, 'bold' : True, 'align' : 'center'})
		header_style = workbook.add_format({'font_name' : 'Times', 'bold' : True, 'left' : 1, 'bottom' : 1, 'right' : 1, 'top' : 1, 'align' : 'center', 'valign' : 'center', 'text_wrap' : 1})
		text_style = workbook.add_format({'font_name' : 'Times', 'left' : 1, 'bottom' : 1, 'right' : 1, 'top' : 1, 'align' : 'left', 'valign' : 'center', 'text_wrap' : 1})
		number_style = workbook.add_format({'font_name' : 'Times', 'left' : 1, 'bottom' : 1, 'right' : 1, 'top' : 1, 'align' : 'right', 'valign' : 'center', 'num_format' : '#,##0'})

		# loop for all selected partners
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
			sheet.set_column('C:C', 20)
			sheet.set_column('D:E', 30)
			sheet.set_column('F:F', 10)
			sheet.set_column('G:I', 14)
			sheet.set_column('J:J', 15)

			# the report title
			# merge the A1 to E1 cell and apply the style font size : 14, font weight bold
			sheet.merge_range('A1:J1', _('Sales Log Report'), title_style)

			# table title
			sheet.write(1, 0, _('Number'), header_style)
			sheet.write(1, 1, _('Invoice / Refund Date'), header_style)
			sheet.write(1, 2, _('Partner'), header_style)
			sheet.write(1, 3, _('Description'), header_style)
			sheet.write(1, 4, _('Ticket Number'), header_style)
			sheet.write(1, 5, _('Company Code'), header_style)
			sheet.write(1, 6, _('Price Unit'), header_style)
			sheet.write(1, 7, _('Other Tax'), header_style)
			sheet.write(1, 8, _('VAT'), header_style)
			sheet.write(1, 9, _('Total'), header_style)

			row = 2
			number = 1

			# search the sales order
			invoices = request.env['account.move'].search([('partner_id', '=', partner.id), ('invoice_date', '>=', wizard.start_date), ('invoice_date', '<=', wizard.end_date)], order="invoice_date")

			for invoice in invoices:
				# the report content
				for line in invoice.invoice_line_ids:
					sheet.write(row, 0, invoice.name, text_style)
					sheet.write(row, 1, dt.strftime(invoice.invoice_date, '%d/%m/%Y'), text_style)
					sheet.write(row, 2, invoice.partner_id.name, text_style)
					sheet.write(row, 3, line.name, text_style)
					sheet.write(row, 4, line.ticket_number if line.ticket_number else '', text_style)
					sheet.write(row, 5, line.supplier.company_code if line.supplier.company_code else '', text_style)
					sheet.write(row, 6, line.price_unit, number_style)
					sheet.write(row, 7, line.other_tax, number_style)
					sheet.write(row, 8, line.amount_tva, number_style)
					sheet.write(row, 9, line.price_total, number_style)

					row += 1
					number += 1

			# create a formula to sum the total sales
			sheet.merge_range('A' + str(row+1) + ':F' + str(row+1), 'Total', text_style)
			sheet.write_formula(row, 6, '=SUM(G3:G' + str(row) + ')', number_style)
			sheet.write_formula(row, 7, '=SUM(H3:H' + str(row) + ')', number_style)
			sheet.write_formula(row, 8, '=SUM(I3:I' + str(row) + ')', number_style)
			sheet.write_formula(row, 9, '=SUM(J3:J' + str(row) + ')', number_style)

		# return the excel file as a response, so the browser can download it
		workbook.close()
		output.seek(0)
		response.stream.write(output.read())
		output.close()

		return response