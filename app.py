import hashlib
import hmac
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
import streamlit as st
import sqlite3
import pandas as pd
import os
from database import create_user
st.set_page_config(
    page_title="Order-to-Audit System",
    page_icon="🏭",
    layout="wide"
)

st.markdown("""
<style>
.st-key-audit_details textarea {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    caret-color: #FFFFFF !important;
}
<style>
/* Production stock success message only */
[class*="st-key-production_stock_status_"] [data-testid="stAlert"] {
    background-color: #145C3A !important;
    border: 1px solid #23834D !important;
}

[class*="st-key-production_stock_status_"] [data-testid="stAlert"] p,
[class*="st-key-production_stock_status_"] [data-testid="stAlert"] span {
    color: #FFFFFF !important;
}
<style>

/* SUCCESS - Green */
div[data-testid="stAlert"][kind="success"] {
    background-color: #E1F4E8 !important;
    border: 1px solid #23834D !important;
}

div[data-testid="stAlert"][kind="success"] p,
div[data-testid="stAlert"][kind="success"] span {
    color: #14532D !important;
}

/* ERROR - Red */
div[data-testid="stAlert"][kind="error"] {
    background-color: #FCE8E8 !important;
    border: 1px solid #C62828 !important;
}

div[data-testid="stAlert"][kind="error"] p,
div[data-testid="stAlert"][kind="error"] span {
    color: #991B1B !important;
}

/* WARNING - Orange */
div[data-testid="stAlert"][kind="warning"] {
    background-color: #FFF1D6 !important;
    border: 1px solid #D97706 !important;
}

div[data-testid="stAlert"][kind="warning"] p,
div[data-testid="stAlert"][kind="warning"] span {
    color: #92400E !important;
}

/* INFO - Blue */
div[data-testid="stAlert"][kind="info"] {
    background-color: #E4F0FC !important;
    border: 1px solid #2874B8 !important;
}

div[data-testid="stAlert"][kind="info"] p,
div[data-testid="stAlert"][kind="info"] span {
    color: #174578 !important;
}

/* Main background */
.stApp {
    background-color: #F4F5F9;
    color: #252B40;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #202747;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

/* Main text */
.stApp p,
.stApp label,
.stApp span,
.stApp li {
    color: #252B40;
}

/* Headings */
h1, h2, h3 {
    color: #202747 !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #D9DFEA;
    padding: 18px;
    border-radius: 12px;
}

/* Metric labels */
[data-testid="stMetricLabel"] {
    color: #505B70 !important;
}

/* Metric values */
[data-testid="stMetricValue"] {
    color: #293B70 !important;
}

/* Buttons */
.stButton > button {
    background-color: #5266A5;
    color: #FFFFFF !important;
    border-radius: 8px;
    border: none;
}

.stButton > button:hover {
    background-color: #394B83;
    color: #FFFFFF !important;
}

/* Tables */
[data-testid="stDataFrame"] {
    border: 1px solid #D9DFEA;
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)

DB_PATH = "data/factory.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def read_data(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
# ---------------- LOGIN AUTHENTICATION ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("Order-to-Audit Management System")
    st.subheader("User Login")

    with st.form("login_form"):

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        login_button = st.form_submit_button("Login")

        if login_button:

            conn = get_connection()

            user = conn.execute(
                """
                SELECT id, username, password, role, is_active
                FROM users
                WHERE username = ?
                """,
                (username.strip(),)
            ).fetchone()

            conn.close()

            if user is None:
                st.error("Invalid username or password.")

            elif not user[4]:
                st.error("This account is inactive.")

            else:
                try:
                    salt, stored_hash = user[2].split("$")

                    entered_hash = hashlib.pbkdf2_hmac(
                        "sha256",
                        password.encode(),
                        salt.encode(),
                        100000
                    ).hex()

                    if hmac.compare_digest(entered_hash, stored_hash):

                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.role = user[3]

                        st.rerun()

                    else:
                        st.error("Invalid username or password.")

                except ValueError:
                    st.error("Password verification failed.")

    st.stop()

# ---------------- END LOGIN AUTHENTICATION ----------------

st.sidebar.title("ORDER TO AUDIT")
st.sidebar.caption("Food Manufacturing Management")

# Display logged-in user
st.sidebar.write(f"User: {st.session_state.username}")
st.sidebar.write(f"Role: {st.session_state.role}")

# Logout button
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.pop("user_id", None)
    st.session_state.pop("username", None)
    st.session_state.pop("role", None)
    st.rerun()

# Role-based page access
role = st.session_state.role

if role == "Admin":
    allowed_pages = [
        "Dashboard",
        "Products",
        "Customers",
        "Inventory",
        "BOM",
        "Orders",
        "Production",
        "Billing",
        "Dispatch",
        "Payment Tracking",
        "Reports",
        "Audit",
        "User Management"
    ]

elif role == "Salesman":
    allowed_pages = [
        "Dashboard",
        "Products",
        "Customers",
        "Orders"
    ]

elif role == "Production Supervisor":
    allowed_pages = [
        "Dashboard",
        "Inventory",
        "BOM",
        "Production"
    ]

elif role == "Accountant/Auditor":
    allowed_pages = [
        "Dashboard",
        "Billing",
        "Payment Tracking",
        "Reports",
        "Audit"
    ]

else:
    st.error("Unauthorized role.")
    st.stop()

page = st.sidebar.radio("Navigation", allowed_pages)

st.title("Order-to-Audit Management System")
st.caption("Integrated Management for Food Manufacturing")



if page == "Dashboard":

    st.subheader("Factory Overview")

    products = read_data("SELECT * FROM products")
    customers = read_data("SELECT * FROM customers")
    orders = read_data("SELECT * FROM orders")
    materials = read_data("SELECT * FROM raw_materials")
    invoices = read_data("SELECT * FROM invoices")
    production = read_data("SELECT * FROM production")
    audit_data = read_data("SELECT * FROM audit_logs")

    total_sales = (
        invoices["grand_total"].sum()
        if not invoices.empty else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Products", len(products))
    c2.metric("Total Customers", len(customers))
    c3.metric("Total Orders", len(orders))
    c4.metric("Total Sales", f"₹{total_sales:,.2f}")

    st.divider()

    c5, c6, c7 = st.columns(3)

    c5.metric("Raw Materials", len(materials))
    c6.metric("Production Batches", len(production))
    c7.metric("Audit Records", len(audit_data))

    st.divider()

    st.subheader("Recent Orders")

    if not orders.empty:
        st.dataframe(
            orders.tail(5),
            use_container_width=True
        )
    else:
        st.info("No orders available yet.")

    st.subheader("Recent Audit Activities")

    if not audit_data.empty:
        st.dataframe(
            audit_data.tail(5),
            use_container_width=True
        )
    else:
        st.info("No audit records available yet.")

elif page == "Products":

    st.subheader("Product Management")

    with st.form("product_form"):
        name = st.text_input("Product Name")
        price = st.number_input("Selling Price", min_value=0.0)
        gst = st.number_input("GST (%)", min_value=0.0, max_value=100.0)
        stock = st.number_input("Opening Stock", min_value=0, step=1)

        submit = st.form_submit_button("Add Product")

        if submit:
            if name.strip():
                conn = get_connection()
                conn.execute(
                    "INSERT INTO products (name, price, gst, stock) VALUES (?, ?, ?, ?)",
                    (name.strip(), price, gst, stock)
                )
                conn.commit()
                conn.close()
                st.success("Product added successfully!")
                st.rerun()
            else:
                st.error("Enter a product name.")

    st.dataframe(read_data("SELECT * FROM products"), use_container_width=True)


elif page == "Customers":

    st.subheader("Customer Management")

    with st.form("customer_form"):
        name = st.text_input("Customer Name")
        state = st.text_input("State")
        customer_type = st.selectbox(
            "Customer Type",
            ["Retailer", "Wholesaler", "Distributor"]
        )

        submit = st.form_submit_button("Add Customer")

        if submit:
            if name.strip():
                conn = get_connection()
                conn.execute(
                    "INSERT INTO customers (name, state, customer_type) VALUES (?, ?, ?)",
                    (name.strip(), state, customer_type)
                )
                conn.commit()
                conn.close()
                st.success("Customer added successfully!")
                st.rerun()
            else:
                st.error("Enter a customer name.")

    st.dataframe(read_data("SELECT * FROM customers"), use_container_width=True)



elif page == "Inventory":

    st.subheader("Raw Material Inventory")

    # ---------------------------------
    # 1. ADD RAW MATERIAL
    # ---------------------------------
    st.markdown("### Add Raw Material")

    with st.form("material_form"):
        name = st.text_input("Material Name")
        material_type = st.selectbox(
            "Material Category",
            ["Raw Material", "Packaging Material"]
        )
        quantity = st.number_input("Opening Quantity", min_value=0.0)
        unit = st.selectbox("Unit", ["kg", "g", "litre", "pieces"])
        rate = st.number_input("Rate per Unit", min_value=0.0)

        submit = st.form_submit_button("Add Material")

        if submit:
            if name.strip():
                conn = get_connection()
                conn.execute(
                    """
                    INSERT INTO raw_materials
                    (name, quantity, unit, rate, material_type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name.strip(), quantity, unit, rate, material_type)
                )
                conn.commit()
                conn.close()

                st.success("Material added successfully!")
                st.rerun()
            else:
                st.error("Enter a material name.")

    st.divider()

    # ---------------------------------
    # 2. SUPPLIER MANAGEMENT
    # ---------------------------------
    st.markdown("### Supplier Management")

    with st.form("supplier_form"):
        supplier_name = st.text_input("Supplier Name")
        contact = st.text_input("Contact Person")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email")
        gstin = st.text_input("GSTIN")
        address = st.text_area("Supplier Address")

        supplier_submit = st.form_submit_button("Add Supplier")

        if supplier_submit:
            if supplier_name.strip():
                conn = get_connection()

                conn.execute(
                    """
                    INSERT INTO suppliers
                    (name, contact, phone, email, gstin, address)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        supplier_name.strip(),
                        contact,
                        phone,
                        email,
                        gstin,
                        address
                    )
                )

                conn.commit()
                conn.close()

                st.success("Supplier added successfully!")
                st.rerun()
            else:
                st.error("Enter supplier name.")

    st.divider()

    # ---------------------------------
    # 3. PURCHASE MANAGEMENT
    # ---------------------------------
    st.markdown("### Record Material Purchase")

    conn = get_connection()

    material_cursor = conn.execute(
        "SELECT * FROM raw_materials ORDER BY name"
    )
    material_columns = [col[0] for col in material_cursor.description]
    materials = [
        dict(zip(material_columns, row))
        for row in material_cursor.fetchall()
    ]

    supplier_cursor = conn.execute(
        "SELECT * FROM suppliers ORDER BY name"
    )
    supplier_columns = [col[0] for col in supplier_cursor.description]
    suppliers = [
        dict(zip(supplier_columns, row))
        for row in supplier_cursor.fetchall()
    ]

    conn.close()

    material_options = {
        f"{m['name']} ({m['unit']}) - ID {m['id']}": m["id"]
        for m in materials
    }

    supplier_options = {
        "No supplier selected": None
    }

    for s in suppliers:
        supplier_options[
            f"{s['name']} - ID {s['id']}"
        ] = s["id"]
    if not material_options:
        st.info("Add a raw material before recording a purchase.")

    else:
        with st.form("purchase_form"):

            selected_material = st.selectbox(
                "Select Material",
                list(material_options.keys())
            )

            selected_supplier = st.selectbox(
                "Select Supplier",
                list(supplier_options.keys())
            )

            purchase_quantity = st.number_input(
                "Purchase Quantity",
                min_value=0.0,
                step=1.0
            )

            purchase_rate = st.number_input(
                "Purchase Rate per Unit",
                min_value=0.0,
                step=1.0
            )

            invoice_no = st.text_input("Supplier Invoice Number")

            purchase_date = st.date_input("Purchase Date")

            purchase_submit = st.form_submit_button(
                "Record Purchase"
            )

            if purchase_submit:

                if purchase_quantity <= 0:
                    st.error("Purchase quantity must be greater than zero.")

                elif purchase_rate <= 0:
                    st.error("Purchase rate must be greater than zero.")

                else:
                    material_id = material_options[selected_material]
                    supplier_id = supplier_options[selected_supplier]

                    total = purchase_quantity * purchase_rate

                    conn = get_connection()

                    try:
                        
                        material_cursor = conn.execute(
                            """
                             SELECT * FROM raw_materials
                            WHERE id = ?
                             """,
                             (material_id,)
                        )

                        material_row = material_cursor.fetchone()

                        if material_row is None:
                                raise ValueError("Selected material was not found.")

                        material = dict(
                            zip(
                                [column[0] for column in material_cursor.description],
                                material_row
                             )
)
                        with conn:
                            cursor = conn.cursor()

                            cursor.execute(
                                """
                                INSERT INTO purchases
                                (
                                    supplier_id,
                                    material_id,
                                    material_name,
                                    material_type,
                                    quantity,
                                    unit,
                                    rate,
                                    total,
                                    invoice_no,
                                    purchase_date
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    supplier_id,
                                    material_id,
                                    material["name"],
                                    material["material_type"],
                                    purchase_quantity,
                                    material["unit"],
                                    purchase_rate,
                                    total,
                                    invoice_no,
                                    str(purchase_date)
                                )
                            )

                            purchase_id = cursor.lastrowid

                            # Automatically increase inventory
                            cursor.execute(
                                """
                                UPDATE raw_materials
                                SET quantity = quantity + ?, rate = ?
                                WHERE id = ?
                                """,
                                (
                                    purchase_quantity,
                                    purchase_rate,
                                    material_id
                                )
                            )

                            # Record stock movement
                            cursor.execute(
                                """
                                INSERT INTO stock_movements
                                (
                                    item_type,
                                    item_id,
                                    item_name,
                                    movement_type,
                                    quantity,
                                    unit,
                                    source_type,
                                    source_id,
                                    notes
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    "raw_material",
                                    material_id,
                                    material["name"],
                                    "PURCHASE_IN",
                                    purchase_quantity,
                                    material["unit"],
                                    "Purchase",
                                    purchase_id,
                                    invoice_no
                                )
                            )

                        st.success(
                            f"Purchase recorded! Total: ₹{total:.2f}. "
                            "Inventory updated successfully."
                        )

                        st.rerun()

                    except Exception as e:
                        st.error(f"Purchase failed: {e}")

                    finally:
                        conn.close()

    st.divider()

    # ---------------------------------
    # 4. CURRENT INVENTORY
    # ---------------------------------
    st.markdown("### Current Inventory")

    st.dataframe(
        read_data("SELECT * FROM raw_materials"),
        use_container_width=True
    )

    st.divider()

    # ---------------------------------
    # 5. PURCHASE HISTORY
    # ---------------------------------
    st.markdown("### Purchase History")

    st.dataframe(
        read_data(
            """
            SELECT
                id,
                material_name,
                material_type,
                quantity,
                unit,
                rate,
                total,
                invoice_no,
                purchase_date
            FROM purchases
            ORDER BY id DESC
            """
        ),
        use_container_width=True
    )

    st.divider()

    # ---------------------------------
    # 6. STOCK MOVEMENT LEDGER
    # ---------------------------------
    st.markdown("### Stock Movement Ledger")

    st.dataframe(
        read_data(
            """
            SELECT
                item_name,
                movement_type,
                quantity,
                unit,
                source_type,
                source_id,
                notes,
                created_at
            FROM stock_movements
            ORDER BY id DESC
            """
        ),
        use_container_width=True
    )


elif page == "BOM":

    st.subheader("Bill of Materials (BOM)")

    st.write(
        "Define the raw materials required to manufacture each product."
    )

    products = read_data("SELECT name FROM products")
    materials = read_data("SELECT name FROM raw_materials")

    if not products.empty and not materials.empty:

        st.markdown("### Add BOM Details")

        with st.form("bom_form"):

            product = st.selectbox(
                "Select Product",
                products["name"].tolist()
            )

            material = st.selectbox(
                "Select Raw Material",
                materials["name"].tolist()
            )

            quantity = st.number_input(
                "Quantity Required Per 1 kg of Product",
                min_value=0.001,
                value=0.70,
                step=0.05
            )

            submit = st.form_submit_button("Save BOM")

            if submit:

                conn = get_connection()

                conn.execute(
                    """
                    INSERT INTO bom
                    (product, material, quantity_per_unit)
                    VALUES (?, ?, ?)
                    """,
                    (product, material, quantity)
                )

                conn.commit()
                conn.close()

                st.success("BOM details saved successfully!")
                st.rerun()

    else:

        st.warning(
            "Please add products and raw materials before creating BOM."
        )

    st.markdown("### Existing BOM Records")

    bom_data = read_data("SELECT * FROM bom")

    if not bom_data.empty:
        st.dataframe(
            bom_data,
            use_container_width=True
        )
    else:
        st.info("No BOM records available.")

elif page == "Orders":

    st.subheader("Sales Order Management")

    customers = read_data("SELECT name FROM customers")
    products = read_data("SELECT name, price FROM products")

    if not customers.empty and not products.empty:

        customer = st.selectbox("Select Customer", customers["name"])
        product = st.selectbox("Select Product", products["name"])

        quantity = st.number_input("Order Quantity", min_value=1, step=1)

        price = float(products.loc[
            products["name"] == product, "price"
        ].iloc[0])

        total = price * quantity

        st.write(f"Order Total: ₹{total:,.2f}")

        if st.button("Place Order"):
            conn = get_connection()
            conn.execute(
                """INSERT INTO orders
                (customer, product, quantity, total, status)
                VALUES (?, ?, ?, ?, ?)""",
                (customer, product, quantity, total, "Pending")
            )
            conn.commit()
            conn.close()
            st.success("Order placed successfully!")
            st.rerun()

    else:
        st.warning("Add at least one customer and one product first.")

    st.subheader("All Orders")
    st.dataframe(read_data("SELECT * FROM orders"), use_container_width=True)
        # Admin Order Approval
    if st.session_state.role == "Admin":

        st.divider()
        st.subheader("Order Approval")

        conn = get_connection()

        pending_cursor = conn.execute(
            """
            SELECT * FROM orders
            WHERE status = 'Pending'
            ORDER BY id DESC
            """
        )

        pending_columns = [
            column[0] for column in pending_cursor.description
        ]

        pending_orders = [
            dict(zip(pending_columns, row))
            for row in pending_cursor.fetchall()
        ]

        conn.close()

        if pending_orders:

            for order in pending_orders:

                with st.expander(
                    f"Order #{order['id']} - {order['customer']}"
                ):

                    st.write(f"Product: {order['product']}")
                    st.write(f"Quantity: {order['quantity']}")
                    st.write(f"Order Total: ₹{order['total']:,.2f}")

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            "Approve Order",
                            key=f"approve_{order['id']}"
                        ):

                            conn = get_connection()

                            conn.execute(
                                """
                                UPDATE orders
                                SET status = 'Approved',
                                    approved_by = ?,
                                    approved_at = CURRENT_TIMESTAMP
                                WHERE id = ? AND status = 'Pending'
                                """,
                                (
                                    st.session_state.username,
                                    order["id"]
                                )
                            )

                            conn.commit()
                            conn.close()

                            st.success("Order approved!")
                            st.rerun()

                    with col2:
                        reason = st.text_input(
                            "Rejection Reason",
                            key=f"reason_{order['id']}"
                        )

                        if st.button(
                            "Reject Order",
                            key=f"reject_{order['id']}"
                        ):

                            if not reason.strip():
                                st.warning("Please enter a rejection reason.")

                            else:
                                conn = get_connection()

                                conn.execute(
                                    """
                                    UPDATE orders
                                    SET status = 'Rejected',
                                        approved_by = ?,
                                        approved_at = CURRENT_TIMESTAMP,
                                        rejection_reason = ?
                                    WHERE id = ? AND status = 'Pending'
                                    """,
                                    (
                                        st.session_state.username,
                                        reason.strip(),
                                        order["id"]
                                    )
                                )

                                conn.commit()
                                conn.close()

                                st.success("Order rejected.")
                                st.rerun()

        else:
            st.info("No pending orders for approval.")

elif page == "Production":
    st.subheader("Production Management")

    products = read_data("SELECT name FROM products")

    if not products.empty:

        product = st.selectbox("Product", products["name"])
        expected = st.number_input("Expected Output (packets)", min_value=1, value=200, step=1)
        actual = st.number_input("Actual Output (packets)", min_value=0, value=188, step=1)

        wastage = max(expected - actual, 0)
        variance = ((actual - expected) / expected) * 100

        # BOM-based material calculation
        st.subheader("Raw Material Requirements")

        bom = read_data(
            "SELECT material, quantity_per_unit FROM bom WHERE product=?",
            (product,)
        )

        
        stock_available = True

        if not bom.empty:

            for _, item in bom.iterrows():

                required = item["quantity_per_unit"] * actual / expected

                stock = read_data(
                    "SELECT quantity, unit FROM raw_materials WHERE name=?",
                    (item["material"],)
                )

                if stock.empty:
                    st.error(f"{item['material']} not found in inventory.")
                    stock_available = False

                else:
                    available = float(stock.iloc[0]["quantity"])
                    unit = stock.iloc[0]["unit"]

                    st.write(
                        f"**{item['material']}** | "
                        f"Required: {required:.2f} {unit} | "
                        f"Available: {available:.2f} {unit}"
                    )

                    if required > available:
                        st.error(f"Insufficient stock: {item['material']}")
                        stock_available = False
                    else:
                        st.success(f"Sufficient stock: {item['material']}")
        # Production expenses
        st.subheader("Production Expenses")
        st.warning("TEST: Production Expenses section is running")

        labour_cost = st.number_input(
            "Labour Cost (₹)", min_value=0.0, value=1200.0
        )

        gas_cost = st.number_input(
            "Gas Cost (₹)", min_value=0.0, value=600.0
        )

        power_cost = st.number_input(
            "Power Cost (₹)", min_value=0.0, value=0.0
        )

        total_overhead = labour_cost + gas_cost + power_cost

        st.metric("Total Production Overhead", f"₹{total_overhead:.2f}")
        # Production performance
        st.subheader("Production Performance")

        st.metric("Wastage", wastage)
        st.metric("Production Variance", f"{variance:.2f}%")

        # Save production record
        if st.button(
            "Save Production Record",
            disabled=(not stock_available or actual <= 0 or expected <= 0 or bom.empty)
        ):
            conn = get_connection()

            try:
                conn.execute("BEGIN")

                # Verify stock before deduction
                for _, item in bom.iterrows():

                    required = item["quantity_per_unit"] * actual / expected

                    result = conn.execute(
                        "SELECT quantity FROM raw_materials WHERE name=?",
                        (item["material"],)
                    ).fetchone()

                    if result is None or float(result[0]) < required:
                        raise ValueError(
                            f"Insufficient stock for {item['material']}"
                        )

                # Deduct raw material stock
                for _, item in bom.iterrows():

                    required = item["quantity_per_unit"] * actual / expected

                    conn.execute(
                        """
                        UPDATE raw_materials
                        SET quantity = quantity - ?
                        WHERE name = ?
                        """,
                        (required, item["material"])
                    )

                # Save production record
                conn.execute(
                    """
                    INSERT INTO production
                    (product, expected_output, actual_output, wastage, variance,
                     labour_cost, gas_cost, power_cost, total_overhead)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product, expected, actual, wastage, variance,
                        labour_cost, gas_cost, power_cost, total_overhead
                    )
                )
                # Update finished goods stock
                conn.execute(
                    """
                    UPDATE products
                    SET stock = stock + ?
                    WHERE name = ?
                    """,
                    (actual, product)
                )

                conn.commit()
                st.success("Production saved and inventory updated!")

            except Exception as e:
                conn.rollback()
                st.error(f"Production not saved: {e}")

            finally:
                conn.close()

            st.rerun()

        # Production history
        st.subheader("Production History")

        st.dataframe(
            read_data("SELECT * FROM production"),
            use_container_width=True
        )

    else:
        st.warning("Add a product before recording production.")

elif page == "Dispatch":

    st.subheader("Dispatch Management")

    conn = get_connection()

    approved_orders = conn.execute("""
        SELECT * FROM orders
        WHERE status = 'Approved'
        ORDER BY id DESC
    """).fetchall()

    columns = [
        col[0] for col in conn.execute(
            "SELECT * FROM orders LIMIT 0"
        ).description
    ]

    approved_orders = [
        dict(zip(columns, row)) for row in approved_orders
    ]

    if approved_orders:

        for order in approved_orders:

            dispatched = conn.execute("""
                SELECT COALESCE(SUM(quantity_dispatched), 0)
                FROM dispatches
                WHERE order_id = ?
            """, (order["id"],)).fetchone()[0]

            remaining = order["quantity"] - dispatched

            if remaining <= 0:
                continue

            with st.expander(
                f"Order #{order['id']} - {order['customer']}"
            ):

                st.write(f"Product: {order['product']}")
                st.write(f"Ordered Quantity: {order['quantity']}")
                st.write(f"Already Dispatched: {dispatched}")
                st.write(f"Remaining Quantity: {remaining}")

                stock_row = conn.execute("""
                    SELECT stock FROM products WHERE name = ?
                """, (order["product"],)).fetchone()

                available_stock = stock_row[0] if stock_row else 0

                st.write(
                    f"Available Finished Stock: {available_stock}"
                )

                dispatch_qty = st.number_input(
                    "Quantity to Dispatch",
                    min_value=1,
                    max_value=remaining,
                    step=1,
                    key=f"dispatch_qty_{order['id']}"
                )

                dispatch_date = st.date_input(
                    "Dispatch Date",
                    key=f"dispatch_date_{order['id']}"
                )

                if st.button(
                    "Confirm Dispatch",
                    key=f"confirm_dispatch_{order['id']}"
                ):

                    if dispatch_qty > available_stock:
                        st.error("Insufficient finished product stock.")

                    else:
                        try:
                            conn.execute("BEGIN")

                            current_stock = conn.execute("""
                                SELECT stock FROM products
                                WHERE name = ?
                            """, (order["product"],)).fetchone()

                            if (
                                current_stock is None
                                or current_stock[0] < dispatch_qty
                            ):
                                raise ValueError(
                                    "Insufficient finished stock."
                                )

                            current_dispatched = conn.execute("""
                                SELECT COALESCE(
                                    SUM(quantity_dispatched), 0
                                )
                                FROM dispatches
                                WHERE order_id = ?
                            """, (order["id"],)).fetchone()[0]

                            if (
                                current_dispatched + dispatch_qty
                                > order["quantity"]
                            ):
                                raise ValueError(
                                    "Dispatch exceeds order quantity."
                                )

                            conn.execute("""
                                UPDATE products
                                SET stock = stock - ?
                                WHERE name = ?
                            """, (dispatch_qty, order["product"]))

                            conn.execute("""
                                INSERT INTO dispatches
                                (
                                    order_id,
                                    customer,
                                    product,
                                    quantity_dispatched,
                                    dispatch_date,
                                    dispatch_status,
                                    dispatched_by
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                order["id"],
                                order["customer"],
                                order["product"],
                                dispatch_qty,
                                str(dispatch_date),
                                "Dispatched",
                                st.session_state.username
                            ))

                            conn.commit()
                            st.success(
                                "Dispatch recorded successfully!"
                            )
                            st.rerun()

                        except Exception as e:
                            conn.rollback()
                            st.error(f"Dispatch failed: {e}")

    else:
        st.info("No approved orders available for dispatch.")

    conn.close()

    st.divider()
    st.subheader("Dispatch History")

    st.dataframe(
        read_data(
            "SELECT * FROM dispatches ORDER BY id DESC"
        ),
        use_container_width=True
    )

elif page == "Payment Tracking":

    st.subheader("Customer Payment Tracking")

    conn = get_connection()

    orders_cursor = conn.execute("""
        SELECT * FROM orders
        WHERE status = 'Approved'
        ORDER BY id DESC
    """)

    columns = [col[0] for col in orders_cursor.description]

    orders = [
        dict(zip(columns, row))
        for row in orders_cursor.fetchall()
    ]

    if orders:

        for order in orders:

            paid = conn.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM payments
                WHERE order_id = ?
            """, (order["id"],)).fetchone()[0]

            balance = order["total"] - paid

            with st.expander(
                f"Order #{order['id']} - {order['customer']}"
            ):

                st.write(f"Product: {order['product']}")
                st.write(f"Order Total: ₹{order['total']:,.2f}")
                st.write(f"Amount Paid: ₹{paid:,.2f}")
                st.write(f"Pending Balance: ₹{balance:,.2f}")

                if balance > 0:

                    st.markdown("**Record New Payment**")

                    amount = st.number_input(
                        "Payment Amount (₹)",
                        min_value=0.01,
                        max_value=float(balance),
                        value=float(balance),
                        step=100.0,
                        key=f"payment_amount_{order['id']}"
                    )

                    payment_date = st.date_input(
                        "Payment Date",
                        key=f"payment_date_{order['id']}"
                    )

                    method = st.selectbox(
                        "Payment Method",
                        ["Cash", "UPI", "Bank Transfer", "Cheque"],
                        key=f"payment_method_{order['id']}"
                    )

                    reference = st.text_input(
                        "Transaction Reference",
                        key=f"payment_reference_{order['id']}"
                    )

                    if st.button(
                        "Record Payment",
                        key=f"record_payment_{order['id']}"
                    ):

                        if amount <= 0 or amount > balance:
                            st.error("Enter a valid payment amount.")

                        else:

                            conn.execute("""
                                INSERT INTO payments
                                (
                                    order_id,
                                    customer,
                                    amount,
                                    payment_date,
                                    payment_method,
                                    reference,
                                    received_by
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                order["id"],
                                order["customer"],
                                amount,
                                str(payment_date),
                                method,
                                reference,
                                st.session_state.username
                            ))

                            conn.commit()
                            conn.close()

                            st.success("Payment recorded successfully!")
                            st.rerun()

                else:
                    st.success("Payment completed. No pending balance.")

    else:
        st.info("No approved orders available for payment tracking.")

    conn.close()

    st.divider()
    st.subheader("Payment History")

    st.dataframe(
        read_data("SELECT * FROM payments ORDER BY id DESC"),
        use_container_width=True
    )

elif page == "Billing":
    st.subheader("Billing Management")

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE,
            customer TEXT,
            product TEXT,
            quantity INTEGER,
            unit_price REAL,
            gst_rate REAL,
            subtotal REAL,
            gst_amount REAL,
            grand_total REAL,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

    customers = read_data("SELECT name FROM customers")
    products = read_data("SELECT name, price, gst FROM products")

    if customers.empty or products.empty:
        st.warning("Please add at least one customer and product first.")

    else:
        customer = st.selectbox(
            "Select Customer",
            customers["name"].tolist()
        )

        product = st.selectbox(
            "Select Product",
            products["name"].tolist()
        )

        quantity = st.number_input(
            "Quantity",
            min_value=1,
            step=1
        )

        product_details = products[
            products["name"] == product
        ].iloc[0]

        price = float(product_details["price"])
        gst_rate = float(product_details["gst"])

        subtotal = price * quantity
        gst_amount = subtotal * gst_rate / 100
        grand_total = subtotal + gst_amount

        st.subheader("Invoice Summary")

        st.write(f"Customer: {customer}")
        st.write(f"Product: {product}")
        st.write(f"Quantity: {quantity}")
        st.write(f"Unit Price: ₹{price:.2f}")
        st.write(f"Subtotal: ₹{subtotal:.2f}")
        st.write(f"GST ({gst_rate}%): ₹{gst_amount:.2f}")

        st.metric("Grand Total", f"₹{grand_total:.2f}")

        if st.button("Generate Invoice"):

            invoice_date = datetime.now()
            date_code = invoice_date.strftime("%Y%m%d")

            conn = get_connection()

            count = conn.execute(
                "SELECT COUNT(*) FROM invoices WHERE invoice_no LIKE ?",
                (f"INV-{date_code}-%",)
            ).fetchone()[0]

            invoice_no = f"INV-{date_code}-{count + 1:04d}"

            conn.execute(
                """INSERT INTO invoices
                (invoice_no, customer, product, quantity,
                 unit_price, gst_rate, subtotal, gst_amount,
                 grand_total, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    invoice_no, customer, product, quantity,
                    price, gst_rate, subtotal, gst_amount,
                    grand_total,
                    invoice_date.strftime("%Y-%m-%d %H:%M:%S")
                )
            )

            conn.commit()
            conn.close()

            buffer = BytesIO()
            pdf = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()

            content = [
                Paragraph("SALES INVOICE", styles["Title"]),
                Spacer(1, 20),
                Paragraph(f"Invoice Number: {invoice_no}", styles["Normal"]),
                Paragraph(
                    f"Date: {invoice_date.strftime('%d-%m-%Y')}",
                    styles["Normal"]
                ),
                Paragraph(f"Customer: {customer}", styles["Normal"]),
                Spacer(1, 20)
            ]

            data = [
                ["Product", "Quantity", "Unit Price", "Amount"],
                [product, str(quantity), f"Rs. {price:.2f}",
                 f"Rs. {subtotal:.2f}"],
                ["", "", f"GST ({gst_rate}%)",
                 f"Rs. {gst_amount:.2f}"],
                ["", "", "Grand Total", f"Rs. {grand_total:.2f}"]
            ]

            content.append(
                Table(data, colWidths=[180, 90, 110, 110])
            )

            pdf.build(content)

            st.session_state["invoice_pdf"] = buffer.getvalue()
            st.session_state["invoice_no"] = invoice_no

            st.success(f"Invoice {invoice_no} generated successfully!")

    if "invoice_pdf" in st.session_state:

        st.download_button(
            label="Download PDF Invoice",
            data=st.session_state["invoice_pdf"],
            file_name=f"{st.session_state['invoice_no']}.pdf",
            mime="application/pdf"
        )

    st.subheader("Invoice History")

    invoice_history = read_data(
        "SELECT * FROM invoices ORDER BY id DESC"
    )

    st.dataframe(
        invoice_history,
        use_container_width=True
    )


elif page == "Reports":

    st.subheader("Business Reports")

    orders = read_data("SELECT * FROM orders")
    products = read_data("SELECT * FROM products")
    materials = read_data("SELECT * FROM raw_materials")
    production = read_data("SELECT * FROM production")
    invoices = read_data("SELECT * FROM invoices")

    st.write("Sales Orders")
    st.dataframe(orders, use_container_width=True)

    st.write("Product Stock")
    st.dataframe(products, use_container_width=True)

    st.write("Raw Material Stock")
    st.dataframe(materials, use_container_width=True)

    st.write("Production Records")
    st.dataframe(production, use_container_width=True)

    st.write("Invoice Records")
    st.dataframe(invoices, use_container_width=True)

    if not orders.empty:
        csv = orders.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Orders CSV",
            csv,
            "orders_report.csv",
            "text/csv"
        )

    if not production.empty:
        production_csv = production.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Production CSV",
            production_csv,
            "production_report.csv",
            "text/csv"
        )

    if not invoices.empty:
        invoice_csv = invoices.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Invoice CSV",
            invoice_csv,
            "invoice_report.csv",
            "text/csv"
        )
elif page == "User Management":

    # Admin-only access
    if st.session_state.role != "Admin":
        st.error("You are not authorized to access this page.")
        st.stop()

    st.subheader("Create New User")

    with st.form("create_user_form"):

        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")

        new_role = st.selectbox(
            "Select Role",
            [
                "Salesman",
                "Production Supervisor",
                "Accountant/Auditor"
            ]
        )

        create_button = st.form_submit_button("Create User")

        if create_button:

            try:
                create_user(new_username, new_password, new_role)
                st.success("User account created successfully!")

            except ValueError as e:
                st.error(str(e))

    st.divider()

    st.subheader("Existing Users")

    users = read_data(
        "SELECT id, username, role, is_active FROM users ORDER BY id"
    )

    st.dataframe(users, use_container_width=True)
elif page == "Audit":

    st.subheader("Audit Management")

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            module TEXT,
            details TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

    st.success("Audit Management is ready!")

st.subheader("Add Audit Record")

with st.form("audit_form"):

    module = st.selectbox(
        "Select Module",
        ["Products", "Inventory", "Orders", "Production", "Billing"]
    )

    action = st.selectbox(
        "Action",
        ["Created", "Updated", "Deleted", "Verified"]
    )

    details = st.text_area("Enter Details", key="audit_details")

    submitted = st.form_submit_button("Save Audit Record")

    if submitted:

        conn = get_connection()

        conn.execute(
            """INSERT INTO audit_logs
            (action, module, details, created_at)
            VALUES (?, ?, ?, ?)""",
            (
                action,
                module,
                details,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()
        conn.close()

        st.success("Audit record saved successfully!")
st.subheader("Audit History")

audit_data = read_data(
    "SELECT * FROM audit_logs ORDER BY id DESC"
)

if audit_data.empty:
    st.info("No audit records available yet.")

else:
    st.dataframe(
        audit_data,
        use_container_width=True
    )        
if not audit_data.empty:

    audit_csv = audit_data.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Audit Report",
        audit_csv,
        "audit_report.csv",
        "text/csv"
    )
