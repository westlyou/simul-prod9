# -*- encoding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
	_inherit = 'account.move'

	# def print_xlsx_sales_log(self):
	# 	return {
	# 		'type' : 'ir.actions.report',
	# 		'report_type' : 'XLSX',
	# 		'date' : {
	# 			'model' : 'Wizard model',
	# 			'output_format' : 'XLSX',
	# 			'options' : json.dumps(data, default=date_utils.json_default),
	# 			'report_name' : 'Excel Report Name'
	# 		}
	# 	}

	def display_amount(self, amount, ndigit=2, th_sep=' ', dec_sep=','):
		"""
			params:
				* amount: The amount to display
				* ndigit: number of decimal digit, by default 2
				* th_sep: thousands separator, by default ','
				* dec_sep: decimal separator, by default '.'
			return:
				formatted_amount: The formatted amount
		"""
		if not amount:
			return "0%s%s" % (dec_sep, ("0" * ndigit))
		else:
			rounded_amount = round(amount, ndigit)
			sign, str_amount = ("", str(rounded_amount)) if rounded_amount > 0 else ("-", str(rounded_amount)[1:])

			split_decimal = str_amount.split('.')

			whole_part = split_decimal[0]
			reversed_amount = whole_part[::-1]
			split_reversed_amount = [reversed_amount[i:i+3] for i in range(0, len(reversed_amount), 3)]
			formatted_whole_part = th_sep.join([item[::-1] for item in split_reversed_amount[::-1]])

			if len(split_decimal) == 2:
				rounded_decimal = round(float("0.%s" % split_decimal[1]), ndigit)
				str_decimal = str(rounded_decimal).split(".")[1]
				str_decimal += "0" * (ndigit - len(str_decimal))
			else:
				str_decimal = "0" * ndigit

			formatted_amount = sign + formatted_whole_part + dec_sep + str_decimal

			return formatted_amount