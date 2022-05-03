# -*- encoding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
	_inherit = 'res.partner'