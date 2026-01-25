# ©  2008-now Terrabit <office(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from datetime import date

from odoo import api, fields, models


class ReportPartnerBalance(models.AbstractModel):
    _name = "report.l10n_ro_balance_confirmation.report_partner_balance"
    _description = "ReportPartnerBalance"
    _template = "l10n_ro_balance_confirmation.report_partner_balance"

    @api.model
    def _get_partner_advances(self, partner, date_to):
        """Get open advance moves for a partner up to date_to."""
        advances = self.env["account.move"].search([
            ("partner_id", "=", partner.id),
            ("date", "<=", date_to),
            ("state", "=", "posted"),
            ("amount_residual", ">", 0),
            ("account_id.account_type", "in", ["asset_other", "liability_other"]),
        ], order="date asc")
        
        result = []
        for move in advances:
            result.append({
                "name": move.name,
                "date": move.date,
                "ref": move.ref or "",
                "account_code": move.account_id.code if move.account_id else "",
                "account_name": move.account_id.name if move.account_id else "",
                "amount_residual": move.amount_residual,
                "move_id": move.id,
            })
        return result

    @api.model
    def _get_partner_invoices(self, partner, date_to):
        """Get open invoice moves for a partner up to date_to."""
        invoices = self.env["account.move"].search([
            ("partner_id", "=", partner.id),
            ("date", "<=", date_to),
            ("state", "=", "posted"),
            ("amount_residual", ">", 0),
            ("account_id.account_type", "in", ["asset_receivable", "liability_payable"]),
        ], order="date asc")
        
        result = []
        for move in invoices:
            paid_amount = move.amount_total - move.amount_residual
            result.append({
                "name": move.name,
                "date": move.date,
                "ref": move.ref or "",
                "move_type": move.move_type,
                "amount_total": move.amount_total,
                "paid_amount": paid_amount,
                "amount_residual": move.amount_residual,
                "move_id": move.id,
            })
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            docids = self.env.context.get("active_ids")
        if not data:
            data = {}
        date_to = data.get("date_to") or self.env.context.get("date_to")
        if not date_to:
            date_to = self.env["ir.config_parameter"].sudo().get_param("l10n_ro_balance_confirmation.date_to")

        if not date_to:
            date_to = date(date.today().year - 1, 12, 31)

        if date_to and isinstance(date_to, str):
            date_to = fields.Date.to_date(date_to)

        # Build partner data with advances and invoices
        partners_data = []
        partners = self.env["res.partner"].browse(docids)
        for partner in partners:
            advances = self._get_partner_advances(partner, date_to)
            invoices = self._get_partner_invoices(partner, date_to)
            
            # Calculate totals
            total_advances = sum(a["amount_residual"] for a in advances)
            total_invoices = sum(i["amount_residual"] for i in invoices)
            total_balance = total_advances + total_invoices
            
            partners_data.append({
                "partner": partner,
                "advances": advances,
                "invoices": invoices,
                "total_advances": total_advances,
                "total_invoices": total_invoices,
                "total_balance": total_balance,
            })

        return {
            "doc_ids": docids,
            "doc_model": "res.partner",
            "data": data,
            "docs": self.env["res.partner"].browse(docids),
            "partners_data": partners_data,
            "date_to": date_to,
        }
