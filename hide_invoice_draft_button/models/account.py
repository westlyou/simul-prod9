# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'