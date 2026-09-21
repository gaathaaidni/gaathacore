from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas


class PDFService:
    """Service for generating PDF documents."""

    def _safe_get(self, source, key, default=""):
        if isinstance(source, dict):
            return source.get(key, default)
        return getattr(source, key, default)

    def generate_pdf(self, template_path: str, data: dict = None) -> BytesIO:
        """Generate a simple PDF document from provided template data."""
        data = data or {}
        buffer = BytesIO()
        canvas = Canvas(buffer, pagesize=letter)
        width, height = letter
        margin = inch
        y = height - margin

        title = self._safe_get(data, "title", "Document")
        subtitle = self._safe_get(data, "subtitle", "")
        lines = self._safe_get(data, "lines", [])

        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawString(margin, y, title)
        y -= 24

        if subtitle:
            canvas.setFont("Helvetica", 12)
            canvas.drawString(margin, y, subtitle)
            y -= 20

        if lines:
            canvas.setFont("Helvetica", 10)
            for line in lines:
                if y < margin + 40:
                    canvas.showPage()
                    y = height - margin
                    canvas.setFont("Helvetica", 10)
                canvas.drawString(margin, y, str(line))
                y -= 16

        canvas.showPage()
        canvas.save()
        buffer.seek(0)
        return buffer

    def generate_invoice_pdf(self, invoice, template_path: str, logo_path: str = None) -> BytesIO:
        """Generate an invoice-specific PDF document."""
        invoice_data = {
            "title": f"Invoice {self._safe_get(invoice, 'number', '')}",
            "subtitle": f"Amount Due: {self._safe_get(invoice, 'total_amount', '')}",
            "lines": [
                f"Invoice ID: {self._safe_get(invoice, 'id', '')}",
                f"Organization ID: {self._safe_get(invoice, 'organization_id', '')}",
                f"Customer: {self._safe_get(self._safe_get(invoice, 'customer', {}), 'name', '')}",
                f"Customer Email: {self._safe_get(self._safe_get(invoice, 'customer', {}), 'email', '')}",
                f"Status: {self._safe_get(invoice, 'status', '')}",
                f"Invoice Date: {self._safe_get(invoice, 'date', '')}",
                f"Due Date: {self._safe_get(invoice, 'due_date', '')}",
                "",
                self._safe_get(invoice, 'notes', ''),
            ],
        }
        return self.generate_pdf(template_path, invoice_data)
