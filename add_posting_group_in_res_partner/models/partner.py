# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
	_inherit = 'res.partner'

	posting_group = fields.Char(string="Posting Group")
	c_posting_group = fields.Char(string="C Posting Group")
	s_posting_group = fields.Char(string="S Posting Group")