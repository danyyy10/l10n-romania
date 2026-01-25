# ©  2008-2022 Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, fields, models
from odoo.exceptions import UserError


class BalanceConfirm(models.TransientModel):
    _name = "l10n_ro.balance_confirm_dialog"
    _description = "Wizard for date input for balance confirmation"

    l10n_ro_balance_date = fields.Date(string="At Date", default=fields.Date.today())
    l10n_ro_balance_type = fields.Selection(
        selection=[("supplier", "Furnizor"), ("client", "Client"), ("all", "Toate")], default="client", string="Tip"
    )
    send_email = fields.Boolean(string="Send by Email", default=False)

    def action_print_balance(self):
        partners = self.env["res.partner"].browse(self.env.context.get("active_ids"))
        if not partners:
            raise UserError(_("No partners selected for balance confirmation."))
        # self = self.with_context(date_to=self.l10n_ro_balance_date)
        # partners = partners.with_context(date_to=self.l10n_ro_balance_date)
        action = self.env.ref("l10n_ro_balance_confirmation.action_report_partner_balance")
        # Curățăm contextul: eliminăm cheia 'date_to' dacă există
        # Curățăm tot contextul și punem doar ce e necesar
        cleaned_context = {
            "lang": self.env.context.get("lang"),
            "tz": self.env.context.get("tz"),
            "uid": self.env.context.get("uid"),
            "allowed_company_ids": self.env.context.get("allowed_company_ids"),
            "active_model": "res.partner",
            "active_ids": partners.ids,
            "active_id": partners.ids[0] if partners else False,
            "date_to": self.l10n_ro_balance_date,  # acesta este critic!
            "type": self.l10n_ro_balance_type,
        }
        
        # Handle email sending
        if self.send_email:
            template = self.env.ref("l10n_ro_balance_confirmation.mail_template_balance_confirmation")
            # Open mail composer with template pre-selected
            return {
                "type": "ir.actions.act_window",
                "res_model": "mail.compose.message",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_composition_mode": "mass_mail",
                    "default_partner_ids": partners.ids,
                    "default_template_id": template.id,
                    "default_model": "res.partner",
                    "date_to": self.l10n_ro_balance_date,
                    "type": self.l10n_ro_balance_type,
                },
            }
        
        # action = action.with_context(date_to=self.l10n_ro_balance_date)
        # pylint: disable=W8121
        return action.with_context(cleaned_context).report_action(
            partners,
            data={
                "date_to": self.l10n_ro_balance_date,
                "doc_ids": partners.ids,
            },
        )
