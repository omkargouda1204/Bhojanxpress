from flask import Blueprint
import base64
from datetime import datetime

template_filters = Blueprint('filters', __name__)

@template_filters.app_template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if not value:
        return ""
    return value.replace('\n', '<br>')

@template_filters.app_template_filter('b64encode')
def b64encode(data):
    """Encode data as base64."""
    if not data:
        return ""
    return base64.b64encode(data).decode('utf-8')

@template_filters.app_template_filter('format_datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """Format a datetime object."""
    if value is None:
        return ""
    return value.strftime(format)

@template_filters.app_template_filter('currency')
def currency(value):
    """Format value as currency."""
    if value is None:
        return "₹0.00"
    return f"₹{float(value):.2f}"
