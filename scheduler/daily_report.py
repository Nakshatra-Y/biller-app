from datetime import date

from database.models import Business
from services.report_service import calculate_daily_report
from services.whatsapp_service import send_daily_report_via_whatsapp


def run_daily_reports(target_date: date | None = None):
    """
    Compute daily reports for all businesses and send them via WhatsApp.

    This function is designed to be triggered by an external scheduler
    (cron, Render cron job, Railway task, etc.).
    """

    businesses = Business.query.all()
    for business in businesses:
        report = calculate_daily_report(business.id, target_date=target_date)
        send_daily_report_via_whatsapp(business, report)

