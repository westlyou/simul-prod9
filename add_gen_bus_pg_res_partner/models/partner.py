# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
	_inherit = 'res.partner'

	gen_bus_pg = fields.Char(string="Gen Bus Posting Group")
	s_gen_bus_pg = fields.Char(string="S Gen Bus Posting Group")
	c_gen_bus_pg = fields.Char(string="C Gen Bus Posting Group")