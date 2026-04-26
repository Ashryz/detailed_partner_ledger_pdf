from odoo import _, models


INVOICE_MOVE_TYPES = ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')


class PartnerLedgerInvoiceProductsHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift=0):
        line = super()._get_report_line_move_line(
            options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift=level_shift,
        )

        if aml_query_result.get('move_type') not in INVOICE_MOVE_TYPES:
            return line

        line['unfoldable'] = True
        line['unfolded'] = line['id'] in options.get('unfolded_lines', []) or options.get('unfold_all')
        line['expand_function'] = '_report_expand_unfoldable_line_invoice_products'
        return line

    def _report_expand_unfoldable_line_invoice_products(
        self, line_dict_id, groupby, options, progress, offset, unfold_all_batch_data=None,
    ):
        report = self.env['account.report'].browse(options['report_id'])
        empty = {'lines': [], 'offset_increment': 0, 'has_more': False, 'progress': progress}

        aml_id = None
        for dummy_markup, model, record_id in report._parse_line_id(line_dict_id):
            if model == 'account.move.line':
                aml_id = record_id

        if not aml_id:
            return empty

        aml = self.env['account.move.line'].browse(aml_id)
        move = aml.move_id
        if move.move_type not in INVOICE_MOVE_TYPES:
            return empty

        product_lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        if not product_lines:
            return empty

        is_debit_side = (aml.debit or 0.0) > 0.0
        company_currency = self.env.company.currency_id
        invoice_currency = move.currency_id
        show_amount_currency = invoice_currency and invoice_currency != company_currency

        lines = [self._build_invoice_products_header_line(report, options, line_dict_id)]
        for pline in product_lines:
            columns = []
            for column in options['columns']:
                label = column['expression_label']
                value = None
                col_currency = False

                if label == 'journal_code':
                    value = self._format_invoice_product_quantity(pline)
                elif label == 'matching_number':
                    value = self._format_invoice_product_unit_price(pline)
                elif label == 'debit' and is_debit_side:
                    value = pline.price_subtotal
                elif label == 'credit' and not is_debit_side:
                    value = pline.price_subtotal
                elif label == 'amount_currency' and show_amount_currency:
                    value = pline.price_subtotal
                    col_currency = invoice_currency

                if value is None or value == '':
                    columns.append(report._build_column_dict(None, None))
                else:
                    columns.append(report._build_column_dict(value, column, options=options, currency=col_currency))

            lines.append({
                'id': report._get_generic_line_id(
                    'account.move.line', pline.id,
                    parent_line_id=line_dict_id, markup='invoice_product',
                ),
                'parent_id': line_dict_id,
                'name': pline.product_id.display_name or pline.name or '',
                'columns': columns,
                'level': 4,
            })

        return {
            'lines': lines,
            'offset_increment': len(lines),
            'has_more': False,
            'progress': progress,
        }

    def _build_invoice_products_header_line(self, report, options, parent_line_id):
        header_labels = {
            'journal_code': _("Quantity"),
            'matching_number': _("Unit Price"),
        }
        columns = []
        for column in options['columns']:
            label = header_labels.get(column['expression_label'])
            if label:
                columns.append(report._build_column_dict(label, column, options=options))
            else:
                columns.append(report._build_column_dict(None, None))
        return {
            'id': report._get_generic_line_id(
                None, None, parent_line_id=parent_line_id, markup='invoice_products_header',
            ),
            'parent_id': parent_line_id,
            'name': _("Product"),
            'columns': columns,
            'level': 4,
            'class': 'fw-bold',
        }

    def _format_invoice_product_quantity(self, product_line):
        qty = product_line.quantity or 0.0
        uom = product_line.product_uom_id.name or ''
        return f"{qty:g} {uom}".strip()

    def _format_invoice_product_unit_price(self, product_line):
        currency = product_line.currency_id or product_line.move_id.currency_id
        return f"{product_line.price_unit:.{currency.decimal_places}f} {currency.symbol}".strip()
