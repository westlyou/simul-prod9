# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplier_type = fields.Selection([
        ('subcontracting', 'Subcontracting'),
        ('company', 'Company')
    ], string="Supplier Type")