# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	refund_ref = fields.Char(string="Refund Reference")