Demo Video: https://drive.google.com/file/d/1IUySFipET1c8oQvCLSxT-NvpiPcgrR4R/view?usp=sharing

# Order-to-Audit Management System

## Project Overview

The **Order-to-Audit Management System** is a web-based application
designed to support the day-to-day operations of a small-scale food
manufacturing business.

It brings key business activities into one application, including
inventory management, purchases, production, customer orders, dispatch,
billing, payment tracking, reporting, and audit records.

The application is built with Python, Streamlit, and SQLite.

## Problem Statement

Small manufacturing businesses may rely on manual registers,
spreadsheets, or separate tools to manage their operations. This can
make it difficult to:

-   Track raw materials, packaging materials, and finished goods.
-   Monitor purchases and stock movements.
-   Connect production consumption with finished-goods output.
-   Review and approve customer orders.
-   Track dispatches, invoices, and customer payments.
-   Maintain accessible business and audit records.

This project aims to provide a centralized system for managing these
activities and improving operational visibility.

## Features

### Dashboard

-   Provides an overview of business operations.
-   Offers navigation to the application's management modules.

### Product and Customer Management

-   Maintain product details.
-   Maintain customer information.
-   View and manage product stock.

### Inventory and Purchase Management

-   Manage raw materials and packaging materials.
-   Maintain supplier information.
-   Record material purchases.
-   View purchase history and stock movement records.

### Bill of Materials (BOM)

-   Define the materials required to manufacture a product.
-   Use BOM requirements when checking production material availability.

### Production Management

-   Record production runs.
-   Check material availability against BOM requirements.
-   Record expected and actual production quantities.
-   Update raw-material and finished-goods stock through production
    transactions.

### Order Management

-   Allow sales users to enter customer orders.
-   Allow administrators to approve or reject pending orders.
-   Maintain order status and approval information.

### Dispatch Management

-   Record full or partial dispatches against approved orders.
-   Check available finished-goods stock.
-   Update finished-goods stock after dispatch.
-   Maintain dispatch history.

### Billing and GST

-   Generate customer invoices.
-   Calculate GST.
-   Generate PDF invoices.
-   Maintain billing records.

### Payment Tracking

-   Record customer payments, including partial payments.
-   Track paid amounts and outstanding balances.
-   Maintain payment history.

### Reports and Audit

-   View business reports.
-   Export supported reports as CSV files.
-   Maintain audit records and transaction history.

### Role-Based Access

The application includes role-based navigation for the following roles:

  Role                    Main areas
  ----------------------- -----------------------------------------------
  Admin                   Overall system management
  Salesman                Products, customers, and orders
  Production Supervisor   Inventory, BOM, and production
  Accountant/Auditor      Billing, payment tracking, reports, and audit

Access should be verified against the current application configuration
before deployment.

## Technology Stack

  Technology   Purpose
  ------------ -----------------------------------------
  Python       Application logic
  Streamlit    Web application interface
  SQLite       Database
  Pandas       Data handling and reporting, where used
  ReportLab    PDF generation, where used
  HTML/CSS     Interface styling

## Project Structure

``` text
Order-to-Audit-System/
├── app.py
├── database.py
├── setup_admin.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/              # Local database; not committed to GitHub
└── venv/              # Local virtual environment; not committed to GitHub
```

The `data/` and `venv/` folders are local runtime folders and should not
be uploaded to the public repository.

## Prerequisites

-   Python 3.10 or later (use the version supported by the installed
    dependencies).
-   Git, if cloning the repository from the command line.
-   A modern web browser.

## Database

The application uses SQLite to store operational records. The database
includes tables for areas such as users, products, customers, raw
materials, suppliers, purchases, BOM, production, orders, dispatches,
and payments.

The database is intended to be initialized locally by the application.
Do not publish a database containing real customer information,
passwords, or other private records.

## Benchmark Demonstration

The project brief includes a Murukku manufacturing and sales benchmark.
The application should be tested against the specified scenario before
the demo is recorded. The benchmark should be demonstrated using actual
application transactions and calculated balances, rather than manually
entering expected closing balances.

Document the verified benchmark results here after completing and
testing the full workflow.

## Known Limitations and Verification

-   Verify all modules and role permissions before using the application
    in a live environment.
-   Verify production quantities and inventory units are consistent (for
    example, kilograms, litres, and packets).
-   Verify GST treatment for intra-state and inter-state transactions.
-   Verify costing rules and overhead allocation before presenting
    cost-per-packet results.
-   Use test data for demonstrations; do not use real customer or
    financial data in a public repository.

## Future Enhancements

Potential future improvements include:

-   More detailed production costing and overhead allocation.
-   Configurable production and stock variance alerts.
-   Expanded GST and financial reports.
-   Stronger audit controls and transaction traceability.
-   Deployment for authorized users to access the application remotely.

## Author

**Sai Muthu Lakshmi**\
Electronics and Communication Engineering Student

## GitHub Repository

[Order-to-Audit Management
System](https://github.com/SAIMUTHULAKSHMI/Order-to-Audit-Management-System)
