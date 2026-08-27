from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import os
from pydantic import BaseModel
from backend.database import get_connection

app = FastAPI()


# =========================================================
# USER MODEL
# =========================================================

class User(BaseModel):
    username: str
    phone_number: str


# =========================================================
# SCAN MODEL
# =========================================================

class Scan(BaseModel):
    user_id: int
    product_name: str
    image_path: str


# =========================================================
# COMPLIANCE RESULT MODEL
# =========================================================

class ComplianceResult(BaseModel):
    scan_id: int

    manufacturer_name: str | None = None
    manufacturer_address: str | None = None

    net_quantity: str | None = None
    mrp: str | None = None

    manufacturing_date: str | None = None
    consumer_care_details: str | None = None

    is_compliant: bool

    violations: str | None = None

class Report(BaseModel):
    scan_id: int
    user_id: int



# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "message": "SIH Backend is running!"
    }


# =========================================================
# GET ALL USERS
# =========================================================

@app.get("/users")
def get_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users;
    """)

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "users": users
    }


# =========================================================
# CREATE USER
# =========================================================

@app.post("/users")
def create_user(user: User):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (
            username,
            phone_number
        )
        VALUES (%s, %s)
        RETURNING user_id;
        """,
        (
            user.username,
            user.phone_number
        )
    )

    user_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "message": "User created successfully",
        "user_id": user_id
    }


# =========================================================
# CREATE SCAN
# =========================================================

@app.post("/scans")
def create_scan(scan: Scan):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO scans (
            user_id,
            product_name,
            image_path
        )
        VALUES (%s, %s, %s)
        RETURNING scan_id;
        """,
        (
            scan.user_id,
            scan.product_name,
            scan.image_path
        )
    )

    scan_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "message": "Scan created successfully",
        "scan_id": scan_id
    }


# =========================================================
# CREATE COMPLIANCE RESULT
# =========================================================

@app.post("/compliance-results")
def create_compliance_result(result: ComplianceResult):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO compliance_results (
            scan_id,
            manufacturer_name,
            manufacturer_address,
            net_quantity,
            mrp,
            manufacturing_date,
            consumer_care_details,
            is_compliant,
            violations
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        RETURNING result_id;
        """,
        (
            result.scan_id,
            result.manufacturer_name,
            result.manufacturer_address,
            result.net_quantity,
            result.mrp,
            result.manufacturing_date,
            result.consumer_care_details,
            result.is_compliant,
            result.violations
        )
    )

@app.post("/reports")
def create_report(report: Report):

    conn = get_connection()
    cursor = conn.cursor()

    # Get compliance information for this scan
    cursor.execute(
        """
        SELECT
            s.product_name,
            c.manufacturer_name,
            c.manufacturer_address,
            c.net_quantity,
            c.mrp,
            c.manufacturing_date,
            c.consumer_care_details,
            c.is_compliant,
            c.violations
        FROM scans s
        JOIN compliance_results c
            ON s.scan_id = c.scan_id
        WHERE s.scan_id = %s;
        """,
        (report.scan_id,)
    )

    data = cursor.fetchone()

    if data is None:
        cursor.close()
        conn.close()

        return {
            "message": "Compliance result not found"
        }

    (
        product_name,
        manufacturer_name,
        manufacturer_address,
        net_quantity,
        mrp,
        manufacturing_date,
        consumer_care_details,
        is_compliant,
        violations
    ) = data

    # Generate actual PDF
    from backend.report_generator import generate_report

    pdf_path = generate_report(
        report_id=report.scan_id,
        product_name=product_name,
        manufacturer_name=manufacturer_name,
        manufacturer_address=manufacturer_address,
        net_quantity=net_quantity,
        mrp=mrp,
        manufacturing_date=manufacturing_date,
        consumer_care_details=consumer_care_details,
        is_compliant=is_compliant,
        violations=violations
    )

    # Store report information in database
    cursor.execute(
        """
        INSERT INTO reports (
            scan_id,
            user_id,
            pdf_path
        )
        VALUES (%s, %s, %s)
        RETURNING report_id;
        """,
        (
            report.scan_id,
            report.user_id,
            pdf_path
        )
    )

    report_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "message": "Report generated successfully",
        "report_id": report_id,
        "pdf_path": pdf_path
    }


@app.get("/users/{user_id}/history")
def get_user_history(user_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            s.scan_id,
            s.product_name,
            s.scan_date,
            c.is_compliant,
            c.violations,
            r.report_id,
            r.pdf_path,
            r.generated_at
        FROM scans s

        LEFT JOIN compliance_results c
            ON s.scan_id = c.scan_id

        LEFT JOIN reports r
            ON s.scan_id = r.scan_id

        WHERE s.user_id = %s

        ORDER BY s.scan_date DESC;
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    history = []

    for row in rows:
        history.append({
            "scan_id": row[0],
            "product_name": row[1],
            "scan_date": row[2],
            "is_compliant": row[3],
            "violations": row[4],
            "report_id": row[5],
            "pdf_path": row[6],
            "generated_at": row[7]
        })

    return {
        "user_id": user_id,
        "history": history
    }

@app.get("/reports/{report_id}")
def get_report(report_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            r.report_id,
            r.scan_id,
            r.user_id,
            r.pdf_path,
            r.generated_at,
            s.product_name,
            s.scan_date
        FROM reports r
        JOIN scans s
            ON r.scan_id = s.scan_id
        WHERE r.report_id = %s;
        """,
        (report_id,)
    )

    report = cursor.fetchone()

    cursor.close()
    conn.close()

    if report is None:
        return {
            "message": "Report not found"
        }

    return {
        "report_id": report[0],
        "scan_id": report[1],
        "user_id": report[2],
        "pdf_path": report[3],
        "generated_at": report[4],
        "product_name": report[5],
        "scan_date": report[6]
    }

@app.get("/reports/{report_id}/download")
def download_report(report_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT pdf_path
        FROM reports
        WHERE report_id = %s;
        """,
        (report_id,)
    )

    report = cursor.fetchone()

    cursor.close()
    conn.close()

    if report is None:
        return {
            "message": "Report not found"
        }

    pdf_path = report[0]

    if not os.path.exists(pdf_path):
        return {
            "message": "PDF file not found"
        }

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"report_{report_id}.pdf"
    )

@app.post("/scans/upload")
async def upload_scan(
    user_id: int = Form(...),
    product_name: str = Form(...),
    image: UploadFile = File(...)
):
    # Create uploads folder
    import os

    os.makedirs("uploads", exist_ok=True)

    # Create file path
    file_path = f"uploads/{image.filename}"

    # Save image
    with open(file_path, "wb") as file:
        file.write(await image.read())

    # Store scan information in database
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO scans (
            user_id,
            product_name,
            image_path
        )
        VALUES (%s, %s, %s)
        RETURNING scan_id;
        """,
        (
            user_id,
            product_name,
            file_path
        )
    )

    scan_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "message": "Scan uploaded successfully",
        "scan_id": scan_id,
        "image_path": file_path
    }

class LoginUser(BaseModel):
    phone_number: str


@app.post("/login")
def login_user(user: LoginUser):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id, username, phone_number, role
        FROM users
        WHERE phone_number = %s;
        """,
        (user.phone_number,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result is None:
        return {
            "message": "User not found"
        }

    return {
        "message": "User found",
        "user_id": result[0],
        "username": result[1],
        "phone_number": result[2],
        "role": result[3]
    }