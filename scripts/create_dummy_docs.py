"""Create dummy test PDFs for finance-demo workspace."""
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

def create_finance_basics_pdf():
    """Create a dummy finance basics PDF."""
    output_path = Path(__file__).parent.parent / "workspaces" / "finance-demo" / "docs" / "finance_basics.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Finance Basics Guide")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "Chapter 1: Interest Rates")
    c.drawString(50, 700, "")
    c.drawString(50, 680, "An interest rate is the percentage charged on a loan amount or paid on savings.")
    c.drawString(50, 660, "It represents the cost of borrowing money or the return on invested funds.")
    c.drawString(50, 640, "Interest rates can be fixed or variable depending on the loan agreement.")
    c.drawString(50, 620, "")
    c.drawString(50, 600, "Types of interest rates:")
    c.drawString(70, 580, "- Simple Interest: Calculated only on the principal amount")
    c.drawString(70, 560, "- Compound Interest: Calculated on principal plus accumulated interest")
    c.drawString(70, 540, "- Annual Percentage Rate (APR): The yearly cost of borrowing")
    
    c.showPage()
    
    # Page 2
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "Chapter 2: Loans and EMI")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "")
    c.drawString(50, 700, "A loan is an amount of money borrowed from a lender that must be repaid with interest.")
    c.drawString(50, 680, "Equated Monthly Installment (EMI) is a fixed payment made by a borrower to a lender")
    c.drawString(50, 660, "at a specified date each month.")
    c.drawString(50, 640, "")
    c.drawString(50, 620, "EMI Components:")
    c.drawString(70, 600, "1. Principal: The original loan amount")
    c.drawString(70, 580, "2. Interest: The cost of borrowing the principal")
    c.drawString(70, 560, "3. Tenure: The duration over which the loan must be repaid")
    c.drawString(50, 540, "")
    c.drawString(50, 520, "The EMI amount depends on three factors: principal amount, interest rate, and tenure.")
    c.drawString(50, 500, "A longer tenure results in lower EMI but higher total interest paid.")
    
    c.showPage()
    
    # Page 3
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "Chapter 3: Credit and Creditworthiness")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "")
    c.drawString(50, 700, "Credit is the ability to borrow money or access goods or services with the understanding")
    c.drawString(50, 680, "that payment will be made in the future.")
    c.drawString(50, 660, "")
    c.drawString(50, 640, "Creditworthiness is an assessment of how likely a borrower is to repay a loan.")
    c.drawString(50, 620, "Lenders evaluate creditworthiness using several factors:")
    c.drawString(70, 600, "- Credit history and credit score")
    c.drawString(70, 580, "- Income and employment stability")
    c.drawString(70, 560, "- Existing debt obligations")
    c.drawString(70, 540, "- Collateral or assets owned")
    c.drawString(50, 520, "")
    c.drawString(50, 500, "Maintaining good creditworthiness helps secure loans at favorable interest rates.")
    
    c.save()
    print(f"Created: {output_path}")


def create_consumer_protection_pdf():
    """Create a dummy consumer protection PDF."""
    output_path = Path(__file__).parent.parent / "workspaces" / "finance-demo" / "docs" / "consumer_protection.pdf"
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Consumer Financial Protection Guidelines")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "Section 1: Your Rights as a Borrower")
    c.drawString(50, 700, "")
    c.drawString(50, 680, "All borrowers have the right to:")
    c.drawString(70, 660, "1. Receive clear information about loan terms and conditions")
    c.drawString(70, 640, "2. Understand the total cost of credit including all fees")
    c.drawString(70, 620, "3. Receive a Key Fact Statement before signing any loan agreement")
    c.drawString(70, 600, "4. Fair treatment without discrimination")
    c.drawString(70, 580, "5. Privacy and protection of personal information")
    c.drawString(50, 560, "")
    c.drawString(50, 540, "Lenders must provide transparent information and cannot hide fees or charges.")
    c.drawString(50, 520, "All terms must be explained in simple, understandable language.")
    
    c.showPage()
    
    # Page 2
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "Section 2: Key Fact Statement (KFS)")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "")
    c.drawString(50, 700, "A Key Fact Statement is a standardized summary of the key terms of a loan.")
    c.drawString(50, 680, "It includes:")
    c.drawString(70, 660, "- Annual Percentage Rate (APR)")
    c.drawString(70, 640, "- Total fees and charges")
    c.drawString(70, 620, "- Loan tenure and repayment schedule")
    c.drawString(70, 600, "- Prepayment terms and penalties")
    c.drawString(70, 580, "- Default consequences")
    c.drawString(50, 560, "")
    c.drawString(50, 540, "The KFS must be given to the borrower before the loan is finalized.")
    c.drawString(50, 520, "Borrowers should carefully review the KFS and ask questions about unclear terms.")
    
    c.showPage()
    
    # Page 3
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "Section 3: Complaint Resolution")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "")
    c.drawString(50, 700, "If you have a complaint about a financial product or service:")
    c.drawString(70, 680, "1. Contact the lender's customer service department first")
    c.drawString(70, 660, "2. If unresolved, escalate to the internal grievance officer")
    c.drawString(70, 640, "3. File a complaint with the financial ombudsman if still unresolved")
    c.drawString(50, 620, "")
    c.drawString(50, 600, "Keep records of all communications and documents related to your complaint.")
    c.drawString(50, 580, "Lenders are required to acknowledge complaints within 7 days and resolve within 30 days.")
    
    c.save()
    print(f"Created: {output_path}")


def create_loan_types_pdf():
    """Create a dummy loan types PDF."""
    output_path = Path(__file__).parent.parent / "workspaces" / "finance-demo" / "docs" / "loan_types.pdf"
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Types of Loans: A Comprehensive Guide")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "1. Personal Loans")
    c.drawString(50, 700, "")
    c.drawString(50, 680, "Personal loans are unsecured loans that can be used for various purposes.")
    c.drawString(50, 660, "They typically have higher interest rates than secured loans.")
    c.drawString(50, 640, "Common uses include debt consolidation, medical expenses, or home improvements.")
    c.drawString(50, 620, "Eligibility is based on credit score, income, and existing debt.")
    c.drawString(50, 600, "")
    c.drawString(50, 580, "2. Home Loans (Mortgages)")
    c.drawString(50, 560, "")
    c.drawString(50, 540, "Home loans are secured loans used to purchase or construct residential property.")
    c.drawString(50, 520, "The property itself serves as collateral for the loan.")
    c.drawString(50, 500, "These loans have longer tenures (typically 15-30 years) and lower interest rates.")
    
    c.showPage()
    
    # Page 2
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "3. Auto Loans")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "")
    c.drawString(50, 700, "Auto loans are secured loans specifically for purchasing vehicles.")
    c.drawString(50, 680, "The vehicle serves as collateral and can be repossessed if payments are missed.")
    c.drawString(50, 660, "Typical tenure is 3-7 years with moderate interest rates.")
    c.drawString(50, 640, "")
    c.drawString(50, 620, "4. Education Loans")
    c.drawString(50, 600, "")
    c.drawString(50, 580, "Education loans help finance tuition, books, and living expenses for students.")
    c.drawString(50, 560, "They often have deferred repayment options until after graduation.")
    c.drawString(50, 540, "Interest rates may be subsidized or lower than other loan types.")
    c.drawString(50, 520, "Some education loans offer tax benefits on interest paid.")
    
    c.showPage()
    
    # Page 3
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "5. Business Loans")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "")
    c.drawString(50, 700, "Business loans provide capital for starting or expanding a business.")
    c.drawString(50, 680, "They can be secured or unsecured depending on the amount and lender.")
    c.drawString(50, 660, "Eligibility requires a business plan and financial projections.")
    c.drawString(50, 640, "")
    c.drawString(50, 620, "Important: Borrowers should carefully compare loan options and choose one that")
    c.drawString(50, 600, "fits their financial situation and repayment capacity. Never borrow more than you")
    c.drawString(50, 580, "can comfortably repay. Read all terms and conditions before signing any agreement.")
    
    c.save()
    print(f"Created: {output_path}")


if __name__ == "__main__":
    try:
        create_finance_basics_pdf()
        create_consumer_protection_pdf()
        create_loan_types_pdf()
        print("\nAll dummy PDFs created successfully!")
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: This script requires reportlab. Install with: pip install reportlab")
