from odoo import fields, models


class DetailedPartnerLedgerWizard(models.TransientModel):
    _name = 'detailed.partner.ledger.wizard'
    _description = ' Detailed Partner Ledger Wizard'

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company,
    )
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection(
        [('posted', 'All Posted Entries'), ('all', 'All Entries')],
        string='Target Moves', required=True, default='posted',
    )
    journal_ids = fields.Many2many('account.journal', string='Journals')
    result_selection = fields.Selection(
        [('customer', 'Receivable Accounts'),
         ('supplier', 'Payable Accounts'),
         ('customer_supplier', 'Receivable and Payable Accounts')],
        string="Partner's", required=True, default='customer_supplier',
    )
    partner_ids = fields.Many2many('res.partner', string='Partners')
    reconciled = fields.Boolean(
        string='Include Reconciled Entries', default=True,
    )
    detailed = fields.Boolean(
        string='Show Invoice Lines', default=False,
        help='When the journal item belongs to a customer or vendor invoice, '
             'display the invoice header and product lines below it.',
    )
    summarized = fields.Boolean(
        string='Summarized', default=False,
        help='Print one row per partner with totals only.',
    )

    def action_print_report(self):
        self.ensure_one()
        data = {
            'form': {
                'date_from': self.date_from.isoformat() if self.date_from else False,
                'date_to': self.date_to.isoformat() if self.date_to else False,
                'target_move': self.target_move,
                'journal_ids': self.journal_ids.ids,
                'result_selection': self.result_selection,
                'partner_ids': self.partner_ids.ids,
                'reconciled': self.reconciled,
                'detailed': self.detailed,
                'summarized': self.summarized,
                'company_id': self.company_id.id,
            },
        }
        return self.env.ref(
            'detailed_partner_ledger_pdf.action_partner_ledger_pdf'
        ).report_action(self, data=data)
