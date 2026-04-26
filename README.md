# Partner Ledger PDF Report

A comprehensive Odoo 18 accounting module that provides an advanced Partner Ledger PDF report with detailed invoice-line information and expandable product lines.

## Overview

The Partner Ledger PDF module extends Odoo's standard accounting reports to offer enhanced visibility into partner transactions. It displays detailed partner ledger entries with the ability to expand invoice lines and view product-level details directly within the report.

## Features

### Core Functionality
- **Detailed Partner Ledger Report**: Comprehensive listing of all partner account transactions
- **Expandable Invoice Lines**: Click to expand invoice entries and view detailed product information
- **Product-Level Details**: Display quantity, unit price, and line subtotals for each invoice product
- **Multi-Currency Support**: Handle transactions in different currencies with proper formatting
- **Flexible Filtering Options**: Filter by date range, partner type, journal, and reconciliation status

### Report Options

The wizard provides the following filtering and display options:

| Option | Description | Default |
|--------|-------------|---------|
| **Start Date** | Beginning date for the report period | - |
| **End Date** | Ending date for the report period | - |
| **Target Moves** | Include only posted entries or all entries (draft + posted) | Posted |
| **Journals** | Filter transactions by specific journals (optional) | All |
| **Partner Type** | Receivable Accounts, Payable Accounts, or Both | Both |
| **Partners** | Filter for specific partners (optional) | All |
| **Include Reconciled Entries** | Include or exclude reconciled transactions | Yes |
| **Show Invoice Lines** | Display invoice headers with product line details | No |
| **Summarized** | Show one row per partner with totals only | No |

### Supported Invoice Types
- Customer Invoices (out_invoice)
- Customer Refunds (out_refund)
- Vendor Invoices (in_invoice)
- Vendor Refunds (in_refund)

## Installation

1. Download or clone the module into your Odoo custom addons directory
2. Update the module list in Odoo: **Settings > Technical > Update Apps List**
3. Search for and install "Partner Ledger PDF"

### Dependencies
- **account**: Core accounting module
- **account_reports**: Enhanced reporting features

## Usage

### Generating the Report

1. Navigate to **Accounting > Reports > Partner Ledger**
2. Click the **Partner Ledger** report button
3. Configure your desired filters in the wizard dialog:
   - Select date range (optional)
   - Choose target moves (posted/all)
   - Select journals (optional)
   - Choose partner account type
   - Select specific partners (optional)
   - Toggle reconciliation filter
   - Enable detailed or summarized view
4. Click **Print** to generate the PDF report

### Viewing Expanded Invoice Details

In detailed mode, invoice entries can be expanded to show product-level information:

1. Open a generated report with "Show Invoice Lines" enabled
2. Click on invoice entries to expand and collapse
3. View product details including:
   - Product name
   - Quantity
   - Unit price
   - Line subtotal

## Technical Structure

### File Organization

```
detailed_partner_ledger_pdf/
├── __init__.py                      # Module initialization
├── __manifest__.py                  # Module metadata and dependencies
├── models/
│   ├── __init__.py
│   └── account_partner_ledger.py   # Invoice product expansion handler
├── report/
│   ├── __init__.py
│   ├── partner_ledger_report.py    # Main report logic and data generation
│   ├── partner_ledger_report.xml   # Report registration
│   └── partner_ledger_template.xml # PDF template
├── wizard/
│   ├── __init__.py
│   ├── partner_ledger_wizard.py    # Filter and parameter wizard
│   └── partner_ledger_wizard_views.xml # Wizard UI definition
└── security/
    └── ir.model.access.csv         # Access control
```

### Key Components

#### Models

**PartnerLedgerInvoiceProductsHandler** (`account_partner_ledger.py`)
- Extends the standard account.partner.ledger.report.handler
- Adds expandable/unfoldable functionality to invoice move lines
- Generates product line details on demand
- Formats quantity and unit price columns
- Handles multi-currency display

**TopfertPartnerLedgerWizard** (`partner_ledger_wizard.py`)
- Transient model for report parameter collection
- Defines all filtering and display options
- Executes report generation with collected data

**ReportTopfertPartnerLedger** (`partner_ledger_report.py`)
- Core report logic and data processing
- Builds SQL queries with dynamic filters
- Resolves account types based on selection
- Generates initial balance calculations
- Formats report output

### Key Methods

**PartnerLedgerInvoiceProductsHandler**
- `_get_report_line_move_line()`: Makes invoice lines unfoldable
- `_report_expand_unfoldable_line_invoice_products()`: Generates expanded product lines
- `_build_invoice_products_header_line()`: Creates column headers for expanded section

**ReportTopfertPartnerLedger**
- `_resolve_account_ids()`: Determines accounts based on partner type selection
- `_build_filters()`: Constructs SQL WHERE clauses from report parameters
- `_lines()`: Fetches and processes move line data

## Configuration

### Access Control

The module includes security rules defined in `security/ir.model.access.csv`. Users must have appropriate permissions to:
- Access partner ledger reports
- View move lines and invoices
- Use the report wizard

### Account Type Mapping

The module maps partner types to account categories:
- **Receivable Accounts**: Customer receivable accounts (asset_receivable)
- **Payable Accounts**: Vendor payable accounts (liability_payable)
- **Both**: Both receivable and payable accounts

## Support & Troubleshooting

### Common Issues

**Report not showing invoice details**
- Ensure "Show Invoice Lines" option is enabled in the wizard
- Verify that transactions are linked to invoices with product lines

**Missing data in report**
- Check that your date range is correct
- Verify partner and journal filters are not too restrictive
- Ensure transactions match the "Target Moves" selection

**Currency display issues**
- Multi-currency support is automatic when invoice currency differs from company currency
- Ensure your company has a proper base currency configured

## Version History

- **18.0.1.0.0**: Initial release for Odoo 18

## Author

**Tarek Ashry**

## License

**LGPL-3** (GNU Lesser General Public License v3)