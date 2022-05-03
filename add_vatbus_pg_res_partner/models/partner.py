# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
	_inherit = 'res.partner'

	vat_bus_pg = fields.Char(string="VAT Bus Posting Group")
	c_vat_bus_pg = fields.Char(string="C VAT Bus Posting Group")
	s_vat_bus_pg = fields.Char(string="S VAT Bus Posting Group")