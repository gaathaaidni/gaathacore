"""
Tax calculation service: compute tax amounts and inclusive/exclusive pricing based on region and tax rules.
"""

def calculate_tax(amount, region, tax_rate, is_inclusive=False):
    """
    Calculate tax for a given amount in a region with a specified rate.
    
    Args:
        amount: base price (float)
        region: region code (str), e.g. 'EU', 'US-CA', 'IN'
        tax_rate: tax percentage (float), e.g. 21.0 for 21%
        is_inclusive: if True, amount includes tax; if False, tax is added
    
    Returns:
        dict with keys: base_price, tax_amount, total_price, is_inclusive
    """
    if is_inclusive:
        # amount is price including tax
        # base_price = amount / (1 + rate/100)
        # tax = amount - base_price
        base = amount / (1 + tax_rate / 100)
        tax = amount - base
        total = amount
    else:
        # amount is base price, tax is added
        # tax = amount * (rate/100)
        # total = amount + tax
        base = amount
        tax = amount * (tax_rate / 100)
        total = amount + tax
    
    return {
        'base_price': round(base, 2),
        'tax_amount': round(tax, 2),
        'total_price': round(total, 2),
        'tax_rate': tax_rate,
        'region': region,
        'is_inclusive': is_inclusive
    }


def get_tax_rules_for_region(db, region):
    """
    Retrieve all active tax rules for a region.
    
    Args:
        db: SQLAlchemy database session
        region: region code (str)
    
    Returns:
        list of TaxRule models
    """
    from models import TaxRule
    return TaxRule.query.filter_by(region=region, active=True).all()


def apply_tax_to_invoice(invoice, region, db):
    """
    Apply tax rules to an invoice and return updated invoice dict with tax breakdown.
    
    Args:
        invoice: dict or Invoice model with 'total' key
        region: region code (str)
        db: SQLAlchemy database session
    
    Returns:
        dict with keys: subtotal, tax_details (list), total_with_tax
    """
    rules = get_tax_rules_for_region(db, region)
    
    if not rules:
        # No tax rules for region; return as-is
        return {
            'subtotal': invoice.get('total', 0) if isinstance(invoice, dict) else invoice.total,
            'tax_details': [],
            'total_with_tax': invoice.get('total', 0) if isinstance(invoice, dict) else invoice.total
        }
    
    subtotal = invoice.get('total', 0) if isinstance(invoice, dict) else invoice.total
    tax_details = []
    total_tax = 0
    
    for rule in rules:
        result = calculate_tax(subtotal, region, rule.rate, rule.is_inclusive)
        tax_details.append({
            'type': rule.tax_type,
            'rate': rule.rate,
            'amount': result['tax_amount']
        })
        total_tax += result['tax_amount']
    
    return {
        'subtotal': round(subtotal, 2),
        'tax_details': tax_details,
        'total_with_tax': round(subtotal + total_tax, 2)
    }
