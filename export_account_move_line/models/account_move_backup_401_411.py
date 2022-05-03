# ############################################################################################################
#                                   This module was created by Muriel Rémi                                   #
#                                         Creation date: 11 June 2021                                        #
# ############################################################################################################
# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError

import ftplib
import os
import pandas as pd
import json
from cryptography.fernet import Fernet
from io import StringIO
from io import BytesIO

from datetime import datetime as dt

class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    exported = fields.Boolean(string="Exported", default=False)

    def export_into_ftp(self):
        __dir__ = os.path.dirname(__file__)

        static_folder_path = os.path.join(os.path.dirname(__dir__), "static")

        # ---------------------------------------------------------------------------------------------
        #                                       Get data from query                                   #
        # ---------------------------------------------------------------------------------------------
        invoices_id = self.env['account.move'].search(['&', ('state', '=', 'posted'), ('move_type', 'in', ('in_invoice', 'out_invoice', 'in_refund', 'out_refund'))]).ids
        # move_lines = self.env['account.move.line'].search(['&', ('exported', '=', False), ('move_id', 'in', invoices_id)])
        move_lines = self.env['account.move.line'].search([('move_id', 'in', invoices_id)])

        if move_lines:
            data = {
                'No ecriture' : [],
                'No ecriture TIERS' : [],
                'No ligne TIERS' : [],
                'No societe THIRDPARTY' : [],
                '1ere ligne document' : [],
                "Nombre d'erreurs document" : [],
                'Nom modele feuille' : [],
                'No ligne' : [],
                'Type de compte' : [],
                'No compte' : [],
                'Date comptabilisation' : [],
                'Type document' : [],
                'No Document' : [],
                'Designation' : [],
                '%TVA' : [],
                'Code devise' : [],
                'Montant' : [],
                'Montant DS' : [],
                'Facteur devise' : [],
                'Remises facture DS' : [],
                "No Donneur/Preneur d'ordre" : [],
                'Groupe comptabilisation' : [],
                'Code departement' : [],
                'Code marque' : [],
                'Code vendeur/acheteur' : [],
                'Code journal' : [],
                'Ecriture systeme' : [],
                "Date d'echeance" : [],
                'Nom feuille' : [],
                'Type comptabilisation' : [],
                'Date document' : [],
                'No Doc. externe' : [],
                'Date compta. immo.' : [],
                'Type compta. immo.' : [],
                "Code loi d'ammortissement" : [],
                'Code etablissement' : [],
                'Zone principale' : [],
                'VIN' : [],
                'No contrat atelier' : [],
                'Exclure ajustement taux de change' : [],
                'Groupe compta marche' : [],
            }

            line_count = {}
            for line in move_lines:
                # if not (line.product_id and line.product_id.category == 'voucher'):
                if line.balance != 0 and line.account_id.code[:3] not in ('401', '411'):
                    origin_order = line.move_id.origin_order()
                    if line.move_id.name not in line_count:
                        line_count[line.move_id.name] = 1
                    else:
                        line_count[line.move_id.name] += 1

                    if line.move_id.move_type == 'in_invoice':
                        designation = 'ACH %s %s' % (line.partner_id.no_g or "", (line.ticket_number or "") if line.move_id.origin_type == 'amadeus' else (line.supplier_invoice_ref or ""))

                        # external_doc = 'F %s' % ((line.ticket_number or "") if line.move_id.origin_type == 'amadeus' else (line.supplier_invoice_ref or ""))

                        if line.move_id.origin_type == 'amadeus':
                            external_doc = ('F %s' % line.ticket_number) if line.ticket_number else ""
                        else:
                            external_doc = ('F %s' % line.supplier_invoice_ref) if line.supplier_invoice_ref else ""
                        # external_doc = ('F %s' % line.ticket_number) if line.move_id.origin_type == 'amadeus' else ('F %s' % (line.supplier_invoice_ref or ""))

                    elif line.move_id.move_type == 'out_invoice':
                        designation = 'Fact %s %s' % (line.partner_id.no_g or "", line.move_id.order_ref or origin_order.ref or "")
                        external_doc = '%s' % (line.move_id.order_ref or origin_order.ref or "")
                    elif line.move_id.move_type == 'out_refund':
                        designation = 'AV %s %s' % (line.partner_id.no_g or "", line.move_id.order_ref or origin_order.ref or "")
                        
                        # refunded = []

                        # out_invoices = self.env['account.move'].search([('move_type', '=', 'out_invoice')])
                        # for invoice in out_invoices:
                        #     if invoice.name in line.move_id.ref:
                        #         refunded.append(invoice)
                        # external_doc = '%s annulee%s' % (", ".join([invoice.name for invoice in refunded]), "s" if len(refunded) > 1 else "")

                        ref_elts = line.move_id.ref.replace(",", " ").replace("/", " ").replace("-", " ").split()
                        refs = [ref for ref in ref_elts if (ref[:2] == '08' and len(ref) == 6) or (ref[:3] == '008' and len(ref) == 7)]
                        ref = refs[0] if len(refs) else None
                        external_doc = ('%s annulee' % ref) if ref else ""

                    elif line.move_id.move_type == 'in_refund':
                        # refunded = []

                        # in_invoices = self.env['account.move'].search([('move_type', '=', 'in_invoice')])
                        # for invoice in in_invoices:
                        #     if invoice.name in line.move_id.ref:
                        #         refunded.append(invoice)

                        # designation = 'RET %s %s' % (line.partner_id.no_g, (line.ticket_number or "") if line.move_id.origin_type == 'amadeus' else (line.supplier_invoice_ref or ""))
                        
                        # external_doc = '%s annulee%s' % (", ".join([invoice.name for invoice in refunded]), "s" if len(refunded) > 1 else "")

                        ref_elts = line.move_id.ref.replace(",", " ").replace("/", " ").replace("-", " ").split()
                        refs = [ref for ref in ref_elts if ref[:3] == '500' and len(ref) == 7]
                        ref = refs[0] if len(refs) else None

                        designation = 'RET %s %s' % (line.partner_id.no_g or "", (line.ticket_number or "") if line.move_id.origin_type == 'amadeus' else ref or "")

                        external_doc = ('%s annulee' % ref) if ref else ""
                    # if line.account_id.code[:3] in ('411', '401'):
                    #     designation = "FCT %s %s - %s" % ("CLT" if line.account_id.code[:3] == '411' else "FRS", line.move_id.name, line.move_id.partner_id.name)
                    # else:
                    #     designation = line.name.split(': ')
                    #     designation = designation[0] if len(designation) == 1 else designation[1]
                    designation = designation[:50].replace("°", " ")
                    external_doc = external_doc[:20].replace("°", " ")

                    # For General Account
                    data['No ecriture'].append(0)
                    data['No ecriture TIERS'].append(line.move_id.name)
                    data['No ligne TIERS'].append(line_count[line.move_id.name])
                    data['No societe THIRDPARTY'].append("SIGM")
                    data['1ere ligne document'].append("")
                    data["Nombre d'erreurs document"].append("")
                    data['Nom modele feuille'].append("")
                    data['No ligne'].append(line_count[line.move_id.name] * 10000)
                    data['Type de compte'].append('General')
                    data['No compte'].append(line.account_id.code)
                    data['Date comptabilisation'].append(dt.strftime(line.date, "%d/%m/%Y"))
                    data['Type document'].append('Facture' if line.move_id.move_type in ('in_invoice', 'out_invoice') else 'Avoir' if line.move_id.move_type in ('in_refund', 'out_refund') else '')
                    data['No Document'].append(line.move_id.name)
                    # data['Designation'].append(line.name)
                    data['Designation'].append(designation)
                    data['%TVA'].append(line.tax_ids.amount)
                    data['Code devise'].append("")
                    data['Montant'].append("")
                    data['Montant DS'].append(line.move_id.display_amount(line.balance, th_sep='', dec_sep=','))
                    data['Facteur devise'].append("")
                    data['Remises facture DS'].append("")
                    data["No Donneur/Preneur d'ordre"].append("")
                    data['Groupe comptabilisation'].append("")
                    data['Code departement'].append("AUTO-SP" if line.move_id.origin_type == 'to' else "AUTO-NV")
                    data['Code marque'].append("MISC LO")
                    data['Code vendeur/acheteur'].append("")
                    data['Code journal'].append("SALES" if line.journal_id.type == 'sale' else "PURCHASES" if line.journal_id.type == 'purchase' else "")
                    data['Ecriture systeme'].append("")
                    data["Date d'echeance"].append('' if not line.date_maturity else dt.strftime(line.date_maturity, "%d/%m/%Y"))
                    data['Nom feuille'].append("")
                    data['Type comptabilisation'].append("Vente" if line.account_id.code[0] == '7' else "")
                    data['Date document'].append(dt.strftime(line.move_id.invoice_date, "%d/%m/%Y"))
                    # data['No Doc. externe'].append("" if not line.move_id.invoice_origin_id.ref else line.move_id.invoice_origin_id.ref[:20])
                    data['No Doc. externe'].append(external_doc)
                    data['Date compta. immo.'].append("")
                    data['Type compta. immo.'].append("")
                    data["Code loi d'ammortissement"].append("")
                    data['Code etablissement'].append('BRANCH01')
                    data['Zone principale'].append("")
                    data['VIN'].append("")
                    data['No contrat atelier'].append("" if not origin_order else origin_order.num_pnr[:20] if line.move_id.origin_type == 'amadeus' else origin_order.name)
                    data['Exclure ajustement taux de change'].append("")
                    data['Groupe compta marche'].append(line.partner_id.gen_bus_pg or "")

                    # For Third Party
                    if line.account_id.code[:3] == '345':
                        data['No ecriture'].append(0)
                        data['No ecriture TIERS'].append(line.move_id.name)
                        line_count[line.move_id.name] += 1
                        data['No ligne TIERS'].append(line_count[line.move_id.name])
                        data['No societe THIRDPARTY'].append("SIGM")
                        data['1ere ligne document'].append("")
                        data["Nombre d'erreurs document"].append("")
                        data['Nom modele feuille'].append("")
                        data['No ligne'].append(line_count[line.move_id.name] * 10000)
                        data['Type de compte'].append('Client' if line.move_id.move_type in ('out_invoice', 'out_refund') else 'Fournisseur' if line.move_id.move_type in ('in_invoice', 'in_refund') else "")
                        data['No compte'].append(line.partner_id.no_g)
                        data['Date comptabilisation'].append(dt.strftime(line.date, "%d/%m/%Y"))
                        data['Type document'].append('Facture' if line.move_id.move_type in ('in_invoice', 'out_invoice') else 'Avoir' if line.move_id.move_type in ('in_refund', 'out_refund') else '')
                        data['No Document'].append(line.move_id.name)
                        # data['Designation'].append(line.name)
                        data['Designation'].append(designation)
                        data['%TVA'].append(line.tax_ids.amount)
                        data['Code devise'].append("")
                        data['Montant'].append("")
                        data['Montant DS'].append(line.move_id.display_amount(-line.balance, th_sep='', dec_sep=','))
                        data['Facteur devise'].append("")
                        data['Remises facture DS'].append("")
                        data["No Donneur/Preneur d'ordre"].append("")
                        data['Groupe comptabilisation'].append(line.partner_id.posting_group or "")
                        data['Code departement'].append("AUTO-SP" if line.move_id.origin_type == 'to' else "AUTO-NV")
                        data['Code marque'].append("MISC LO")
                        data['Code vendeur/acheteur'].append("")
                        data['Code journal'].append("SALES" if line.journal_id.type == 'sale' else "PURCHASES" if line.journal_id.type == 'purchase' else "")
                        data['Ecriture systeme'].append("")
                        data["Date d'echeance"].append('' if not line.date_maturity else dt.strftime(line.date_maturity, "%d/%m/%Y"))
                        data['Nom feuille'].append("")
                        data['Type comptabilisation'].append("Vente" if line.account_id.code[0] == '7' else "")
                        data['Date document'].append(dt.strftime(line.move_id.invoice_date, "%d/%m/%Y"))
                        # data['No Doc. externe'].append("" if not line.move_id.invoice_origin_id.ref else line.move_id.invoice_origin_id.ref[:20])
                        data['No Doc. externe'].append(external_doc)
                        data['Date compta. immo.'].append("")
                        data['Type compta. immo.'].append("")
                        data["Code loi d'ammortissement"].append("")
                        data['Code etablissement'].append('BRANCH01')
                        data['Zone principale'].append("")
                        data['VIN'].append("")
                        data['No contrat atelier'].append("" if not origin_order else origin_order.num_pnr[:20] if line.move_id.origin_type == 'amadeus' else origin_order.name)
                        data['Exclure ajustement taux de change'].append("")
                        data['Groupe compta marche'].append(line.partner_id.gen_bus_pg or "")

            df = pd.DataFrame(data)
            # ----------------------------------------------

            buffer = StringIO()
            df.to_csv(buffer, sep=';', index=False, header=False, line_terminator="\n")
            text = buffer.getvalue()
            bio = BytesIO(str.encode(text))
            bcp_bio = BytesIO(str.encode(text))

            # ---------------------------------------------------------------------------------------------
            #                      Send the generated CSV file into the FTP server                        #
            # ---------------------------------------------------------------------------------------------

            # Initialization
            _CONFIG_ = None
            _KEY_ = b'_Eb-ez6gdiB8bU89Y8cwl9LlGFC_0Mbv1CbLS8qNVio='
            _PASSWORD_DECRYPTED_ = False

            with open(static_folder_path + "/config.json") as json_data_file:
                _CONFIG_ = json.load(json_data_file)

            fernet = Fernet(_KEY_)

            _CONFIG_['ftp']['password'] = fernet.decrypt(bytes(_CONFIG_['ftp']['password'], 'utf-8'))
            _CONFIG_['ftp']['password'] = _CONFIG_['ftp']['password'].decode('utf-8')

            # Connecting to the FTP Server
            session = ftplib.FTP(_CONFIG_['ftp']['host'], _CONFIG_['ftp']['username'], _CONFIG_['ftp']['password'], timeout=100000)

            # Browsing into the destination folder
            session.cwd(_CONFIG_['csvfiles']['dest'])

            # Sending the file
            try:
                exported_filename = 'COMPTA_POUR_INCADEA_%s.txt' % dt.strftime(dt.now(), '%Y%m%d%H%M%S')
            #     session.storbinary('STOR %s' % exported_filename, bio)
            #     move_lines.write({'exported' : True})
            except Exception as e:
                print("{} Erreur : Cannot upload the file to the SFTP server.\n{}".format(dt.now(), e))

            # session.quit()

            # Backup
            _BCP_CONFIG_ = None
            with open(static_folder_path + "/backup_config.json") as bcp_json_file:
                _BCP_CONFIG_ = json.load(bcp_json_file)

            fernet = Fernet(_KEY_)

            _BCP_CONFIG_['ftp']['password'] = fernet.decrypt(bytes(_BCP_CONFIG_['ftp']['password'], 'utf-8'))
            _BCP_CONFIG_['ftp']['password'] = _BCP_CONFIG_['ftp']['password'].decode('utf-8')

            bcp_session = ftplib.FTP(_BCP_CONFIG_['ftp']['host'], _BCP_CONFIG_['ftp']['username'], _BCP_CONFIG_['ftp']['password'], timeout=100000)

            bcp_session.cwd(_BCP_CONFIG_['csvfiles']['dest'])
            bcp_session.storbinary('STOR %s' % exported_filename, bcp_bio)

            bcp_session.quit()