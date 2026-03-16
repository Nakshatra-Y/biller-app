from database.models import Business


def send_daily_report_via_whatsapp(business: Business, report: dict):
    """
    Placeholder for WhatsApp integration.

    In production you can integrate with a provider like Twilio or Meta's
    WhatsApp Cloud API here and send the report summary to the cafe owner.
    """

    summary = (
        f"Daily Sales Report for {business.name}\n"
        f"Date: {report['date']}\n"
        f"Total Bills: {report['total_bills']}\n"
        f"Total Sales: {report['total_sales']}\n"
        f"Top Item: {report['top_item'] or 'N/A'}"
    )
    # For now we just print; replace with real API call later.
    print(summary)

