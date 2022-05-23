# ############################################################################################################
#                                   This module was created by Muriel Rémi                                   #
#                                       Creation date: 18 November 2021                                      #
# ############################################################################################################
# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = "res.partner"

    in_group = fields.Boolean(string="Group", compute="_compute_group")

    @api.depends('c_gen_bus_pg')
    def _compute_group(self):
        for record in self:
            # record.in_group = record.c_posting_group == 'C10'
            record.in_group = record.c_gen_bus_pg == 'C10'