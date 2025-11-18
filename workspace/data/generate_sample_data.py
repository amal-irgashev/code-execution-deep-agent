#!/usr/bin/env python3
"""Generate sample data files for demo purposes.

Creates:
1. orders.csv - Large CSV with 10,000+ order records
2. sample_form.pdf - PDF with fillable form fields
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from pypdf import PdfWriter


def generate_orders_csv(output_path: Path, num_rows: int = 10000):
    """Generate a sample orders CSV file.

    Args:
        output_path: Path to save CSV file.
        num_rows: Number of order rows to generate.
    """
    print(f"Generating {num_rows} order records...")

    # Customer names pool
    first_names = [
        "James",
        "Mary",
        "John",
        "Patricia",
        "Robert",
        "Jennifer",
        "Michael",
        "Linda",
        "William",
        "Elizabeth",
        "David",
        "Barbara",
        "Richard",
        "Susan",
        "Joseph",
        "Jessica",
        "Thomas",
        "Sarah",
        "Charles",
        "Karen",
    ]
    last_names = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Rodriguez",
        "Martinez",
    ]

    # Generate data
    data = []
    start_date = datetime(2023, 1, 1)

    for i in range(num_rows):
        order_id = f"ORD-{i+1:06d}"
        customer = f"{random.choice(first_names)} {random.choice(last_names)}"

        # Amount with some high values for filtering demo
        if random.random() < 0.05:  # 5% high-value orders
            amount = random.uniform(5000, 50000)
        else:
            amount = random.uniform(10, 2000)

        # Random date within 2023-2024
        days_offset = random.randint(0, 700)
        order_date = start_date + timedelta(days=days_offset)

        status = random.choice(["pending", "shipped", "delivered", "cancelled"])

        data.append(
            {
                "order_id": order_id,
                "customer": customer,
                "amount": round(amount, 2),
                "date": order_date.strftime("%Y-%m-%d"),
                "status": status,
            }
        )

    # Create DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"✓ Created {output_path} with {len(df)} rows")

    # Print some stats
    print(f"  - Amount range: ${df['amount'].min():.2f} - ${df['amount'].max():.2f}")
    print(f"  - High-value orders (>$5000): {len(df[df['amount'] > 5000])}")


def generate_sample_form_pdf(output_path: Path):
    """Generate a simple PDF with form fields using reportlab.

    Args:
        output_path: Path to save PDF file.
    """
    print("Generating sample PDF with form fields...")

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfform

        # Create PDF with form fields using reportlab
        c = canvas.Canvas(str(output_path), pagesize=letter)

        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "Sample Contact Information Form")

        # Add form fields
        c.setFont("Helvetica", 12)

        # Name field
        c.drawString(50, 700, "Name:")
        form = c.acroForm
        form.textfield(
            name="Name",
            tooltip="Full Name",
            x=150,
            y=695,
            width=300,
            height=20,
            borderWidth=1,
            value="John Doe",
        )

        # Email field
        c.drawString(50, 650, "Email:")
        form.textfield(
            name="Email",
            tooltip="Email Address",
            x=150,
            y=645,
            width=300,
            height=20,
            borderWidth=1,
            value="john.doe@example.com",
        )

        # Address field
        c.drawString(50, 600, "Address:")
        form.textfield(
            name="Address",
            tooltip="Street Address",
            x=150,
            y=595,
            width=300,
            height=20,
            borderWidth=1,
            value="123 Main Street, Anytown, ST 12345",
        )

        # Phone field
        c.drawString(50, 550, "Phone:")
        form.textfield(
            name="Phone",
            tooltip="Phone Number",
            x=150,
            y=545,
            width=300,
            height=20,
            borderWidth=1,
            value="(555) 123-4567",
        )

        # Company field
        c.drawString(50, 500, "Company:")
        form.textfield(
            name="Company",
            tooltip="Company Name",
            x=150,
            y=495,
            width=300,
            height=20,
            borderWidth=1,
            value="Acme Corporation",
        )

        c.save()
        print(f"✓ Created {output_path} with 5 form fields")

    except ImportError:
        print("Warning: reportlab not installed, creating simple PDF without forms")
        # Fallback: create a simple PDF with text content
        pdf_writer = PdfWriter()
        pdf_writer.add_blank_page(width=612, height=792)

        with open(output_path, "wb") as output_file:
            pdf_writer.write(output_file)

        print(f"✓ Created {output_path} (basic PDF without forms)")


def main():
    """Generate all sample data files."""
    # Ensure data directory exists
    data_dir = Path(__file__).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    # Generate CSV
    csv_path = data_dir / "orders.csv"
    generate_orders_csv(csv_path, num_rows=10000)

    # Generate PDF
    pdf_path = data_dir / "sample_form.pdf"
    generate_sample_form_pdf(pdf_path)

    print("\n✓ All sample data files generated successfully!")


if __name__ == "__main__":
    main()

