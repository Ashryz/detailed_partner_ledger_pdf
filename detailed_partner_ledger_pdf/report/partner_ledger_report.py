from odoo import api, models, _
from odoo.exceptions import UserError


ACCOUNT_TYPE_BY_SELECTION = {
    'customer': ('asset_receivable',),
    'supplier': ('liability_payable',),
    'customer_supplier': ('asset_receivable', 'liability_payable'),
}

INVOICE_MOVE_TYPES = ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')


class ReportPartnerLedger(models.AbstractModel):
    _name = 'report.detailed_partner_ledger_pdf.report_partner_ledger'
    _description = 'Partner Ledger PDF'

    def _resolve_account_ids(self, data):
        types = ACCOUNT_TYPE_BY_SELECTION[data['form']['result_selection']]
        company_id = data['form'].get('company_id') or self.env.company.id
        accounts = self.env['account.account'].search([
            ('account_type', 'in', list(types)),
            ('deprecated', '=', False),
            ('company_ids', 'in', company_id),
        ])
        return accounts.ids

    def _build_filters(self, data, partner_id=None, for_initial=False):
        form = data['form']
        clauses = ['aml.company_id = %s']
        params = [form.get('company_id') or self.env.company.id]

        if form.get('target_move') == 'posted':
            clauses.append("aml.parent_state = 'posted'")
        else:
            clauses.append("aml.parent_state IN ('draft', 'posted')")

        clauses.append('aml.account_id IN %s')
        params.append(tuple(data['computed']['account_ids']))

        if partner_id is not None:
            clauses.append('aml.partner_id = %s')
            params.append(partner_id)
        else:
            clauses.append('aml.partner_id IS NOT NULL')

        if form.get('journal_ids'):
            clauses.append('aml.journal_id IN %s')
            params.append(tuple(form['journal_ids']))

        if form.get('partner_ids') and partner_id is None:
            clauses.append('aml.partner_id IN %s')
            params.append(tuple(form['partner_ids']))

        if for_initial:
            if form.get('date_from'):
                clauses.append('aml.date < %s')
                params.append(form['date_from'])
        else:
            if form.get('date_from'):
                clauses.append('aml.date >= %s')
                params.append(form['date_from'])
            if form.get('date_to'):
                clauses.append('aml.date <= %s')
                params.append(form['date_to'])

        if not form.get('reconciled'):
            clauses.append('aml.full_reconcile_id IS NULL')

        return ' AND '.join(clauses), params

    def _lines(self, data, partner):
        if not data['computed']['account_ids']:
            return []
        where_clause, params = self._build_filters(data, partner_id=partner.id)
        query = """
            SELECT aml.id,
                   aml.date,
                   aml.date_maturity,
                   aml.ref,
                   aml.name,
                   aml.debit,
                   aml.credit,
                   aml.move_id,
                   aml.account_id,
                   j.code AS j_code,
                   m.name AS move_name,
                   m.move_type AS m_type
              FROM account_move_line aml
              LEFT JOIN account_journal j ON aml.journal_id = j.id
              LEFT JOIN account_move m ON aml.move_id = m.id
             WHERE """ + where_clause + """
             ORDER BY aml.date, aml.move_id, aml.date_maturity
        """
        self.env.cr.execute(query, params)
        rows = self.env.cr.dictfetchall()

        account_ids = list({r['account_id'] for r in rows if r['account_id']})
        accounts_by_id = {
            a.id: a for a in self.env['account.account'].browse(account_ids)
        }

        invoice_ids = list({
            r['move_id'] for r in rows if r['m_type'] in INVOICE_MOVE_TYPES
        })
        invoices = {
            inv.id: inv
            for inv in self.env['account.move'].browse(invoice_ids)
        } if invoice_ids else {}

        AML = self.env['account.move.line']
        running = 0.0
        full = []
        for r in rows:
            account = accounts_by_id.get(r['account_id'])
            r['a_code'] = account.code if account else ''
            r['a_name'] = account.name if account else ''
            r['displayed_name'] = ' - '.join(
                v for v in (r['move_name'], r['ref'], r['name'])
                if v not in (None, '', '/')
            )
            running += (r['debit'] or 0.0) - (r['credit'] or 0.0)
            r['progress'] = running
            invoice = invoices.get(r['move_id']) if r['m_type'] in INVOICE_MOVE_TYPES else False
            r['invoice'] = invoice
            r['ilines'] = invoice.invoice_line_ids.filtered(
                lambda l: l.display_type == 'product'
            ) if invoice else AML
            full.append(r)
        return full

    def _sum_partner(self, data, partner):
        empty = {'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
        if not data['computed']['account_ids']:
            return empty
        where_clause, params = self._build_filters(data, partner_id=partner.id)
        query = """
            SELECT COALESCE(SUM(aml.debit), 0.0)  AS debit,
                   COALESCE(SUM(aml.credit), 0.0) AS credit
              FROM account_move_line aml
             WHERE """ + where_clause
        self.env.cr.execute(query, params)
        res = self.env.cr.dictfetchone() or {'debit': 0.0, 'credit': 0.0}
        res['balance'] = (res['debit'] or 0.0) - (res['credit'] or 0.0)
        return res

    def _get_initial_balance(self, data, partner):
        empty = {'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
        if not data['form'].get('date_from') or not data['computed']['account_ids']:
            return empty
        where_clause, params = self._build_filters(
            data, partner_id=partner.id, for_initial=True,
        )
        query = """
            SELECT COALESCE(SUM(aml.debit), 0.0)  AS debit,
                   COALESCE(SUM(aml.credit), 0.0) AS credit
              FROM account_move_line aml
             WHERE """ + where_clause
        self.env.cr.execute(query, params)
        res = self.env.cr.dictfetchone() or {'debit': 0.0, 'credit': 0.0}
        res['balance'] = (res['debit'] or 0.0) - (res['credit'] or 0.0)
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data or not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        company = self.env['res.company'].browse(
            data['form'].get('company_id') or self.env.company.id
        )
        data['computed'] = {
            'account_ids': self._resolve_account_ids(data),
        }

        if data['form'].get('partner_ids'):
            partner_ids = list(data['form']['partner_ids'])
        elif not data['computed']['account_ids']:
            partner_ids = []
        else:
            where_clause, params = self._build_filters(data, partner_id=None)
            query = """
                SELECT DISTINCT aml.partner_id
                  FROM account_move_line aml
                 WHERE """ + where_clause
            self.env.cr.execute(query, params)
            partner_ids = [row[0] for row in self.env.cr.fetchall() if row[0]]

        partners = self.env['res.partner'].browse(partner_ids).sorted(
            key=lambda p: ((p.ref or ''), (p.name or ''))
        )

        return {
            'doc_ids': partner_ids,
            'doc_model': 'res.partner',
            'data': data,
            'docs': partners,
            'company': company,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
            'get_initial_balance': self._get_initial_balance,
        }
