# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    other_tax = fields.Float(string="Other Tax", compute="_amount_all", compute_sudo=True)
    amount_tva = fields.Float(string="Amount TVA", compute="_amount_all", compute_sudo=True)

    travel_order_id = fields.Many2one('travel.order', string="Travel Order", readonly=True)

    origin_type = fields.Selection([
        ('amadeus', 'Ticketing'),
        ('to', 'Tour Operator')
    ], string="Origin Type")

    ref = fields.Char(string="Reference")

    @api.depends('amount_total', 'amount_untaxed', 'order_line.other_tax')
    def _amount_all(self):
        super(PurchaseOrder, self)._amount_all()
        for order in self:
            other_tax = 0.0
            amount_tva = order.amount_total - order.amount_untaxed
            for line in order.order_line:
                other_tax += line.other_tax

            order.update({
                'other_tax' : order.currency_id.round(other_tax),
                'amount_tva' : amount_tva,
                'amount_total' : order.amount_total + order.currency_id.round(other_tax),
            })

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()

        invoice_vals.update({
            'origin_type' : self.origin_type,
            'order_ref' : self.ref,
        })

        return invoice_vals

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    other_tax = fields.Float(string="Other Tax")

    supplier_invoice_ref = fields.Char(string="Supplier invoice ref")
    passenger = fields.Char(string="Passenger")
    ticket_number = fields.Char(string="Ticket Number")
    journey = fields.Char(string="Journey")
    flight_number = fields.Char(string="Flight number")
    flight_class = fields.Char(string="Flight class")

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'other_tax')
    def _compute_amount(self):
        super(PurchaseOrderLine, self)._compute_amount()
        for line in self:
            line.update({
                'price_total' : line.price_total + line.other_tax,
            })

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)

        # raise UserError(str(res))
        res.update({
            'other_tax' : self.other_tax,
            'supplier_invoice_ref' : self.supplier_invoice_ref,
            'passenger' : self.passenger,
            'ticket_number' : self.ticket_number,
            'journey' : self.journey,
            'flight_num' : self.flight_number,
            'flight_class' : self.flight_class,
        })

        return res