# ############################################################################################################
#                                   This module was created by Muriel Rémi                                   #
#                                       Creation date: 09 December 2021                                      #
# ############################################################################################################
# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError

from datetime import datetime as dt

from functools import partial
from odoo.tools.misc import formatLang

class AccountMove(models.Model):
    _inherit = 'account.move'

    global_label = fields.Text(string="Global Label", compute="_get_global_label")
    # other_tax = fields.Float(string="Amount Tax", compute="_compute_other_tax")

    invoice_origin_id = fields.Many2one('travel.order', "Invoice Origin")
    # order_ref = fields.Char(string="Order Reference", related="invoice_origin_id.ref")
    order_ref = fields.Char(string="Order Reference")

    # def write(self, vals):
    #     raise UserError(str(vals))

    def _get_global_label(self):
        for record in self:
            # linked_sale = self.env['sale.order'].search([('name', '=', record.invoice_origin)])
            linked_travel = self.env['travel.order'].search([('name', '=', record.invoice_origin)])

            if linked_travel.id:
                record.global_label = linked_travel.global_label
            else:
                record.global_label = ""

    @api.model
    def create(self, vals):
        # Save new fields
        if 'invoice_line_ids' in vals:
            for invoice_line in vals['invoice_line_ids']:
                if 'line_ids' in vals:
                    corresponding_lines = [line for line in vals['line_ids'] if line[1] == invoice_line[1]]
                    if corresponding_lines:
                        corresponding_line = corresponding_lines[0]
                        corresponding_line[2].update({
                            'supplier' : None if not 'supplier' in invoice_line[2] else invoice_line[2]['supplier'],
                            'passenger' : "" if not 'passenger' in invoice_line[2] else invoice_line[2]['passenger'],
                            'ticket_number' : "" if not 'ticket_number' in invoice_line[2] else invoice_line[2]['ticket_number'],
                            'journey' : "" if not 'journey' in invoice_line[2] else invoice_line[2]['journey'],
                        })

        # set invoice_origin
        # if 'order_ref' in vals and vals['order_ref'].split():
        #     order = self.env['travel.order'].search([('ref', '=', vals['order_ref'])])
        #     if order:
        #         vals.update({
        #             'invoice_origin' : order.name,
        #             'invoice_origin_id' : order.id
        #         })
        #     else:
        #         raise UserError(_("Order Reference %s not found!") % vals['order_ref'])
        return super(AccountMove, self).create(vals)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    flight_num = fields.Char(string="Flight Number")
    flight_class = fields.Char(string="Flight Class")
    supplier = fields.Many2one('res.partner', string="Supplier")
    ticket_number = fields.Char(string="Ticket Number")
    journey = fields.Char(string="Journey")
    passenger = fields.Char(string="Passenger")

    supplier_invoice_ref = fields.Char(string="Supplier invoice reference")

    amount_tva = fields.Float(string="Montant TVA", compute="_compute_vat")

    @api.depends('price_total', 'price_subtotal')
    def _compute_vat(self):
        for record in self:
            record.amount_tva = record.price_total - record.price_subtotal