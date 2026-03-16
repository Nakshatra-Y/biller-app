from datetime import datetime, date, timedelta

from sqlalchemy import func

from database.models import Bill, BillItem


def _range_for_days(days_back: int):
    end = datetime.combine(date.today(), datetime.max.time())
    start = end - timedelta(days=days_back - 1)
    return start, end


def calculate_daily_report(business_id: int, target_date: date | None = None):
    if target_date is None:
        target_date = date.today()

    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())

    bills = (
        Bill.query.filter(
            Bill.business_id == business_id,
            Bill.status == "COMPLETED",
            Bill.completed_at >= start_dt,
            Bill.completed_at <= end_dt,
        )
        .order_by(Bill.completed_at.asc())
        .all()
    )

    total_bills = len(bills)
    total_sales = sum(b.total for b in bills)

    item_counts: dict[str, int] = {}
    table_counts: dict[str, int] = {}
    for bill in bills:
        table_counts[bill.table_no] = table_counts.get(bill.table_no, 0) + 1
        for item in bill.items:
            item_counts[item.product_name] = item_counts.get(item.product_name, 0) + item.quantity

    top_item = max(item_counts.items(), key=lambda kv: kv[1])[0] if item_counts else None
    most_active_table = max(table_counts.items(), key=lambda kv: kv[1])[0] if table_counts else None
    avg_bill = total_sales / total_bills if total_bills else 0.0

    return {
        "date": target_date.isoformat(),
        "total_bills": total_bills,
        "total_sales": total_sales,
        "top_item": top_item,
        "avg_bill": avg_bill,
        "most_active_table": most_active_table,
    }


def build_analytics_payload(business_id: int):
    today = date.today()
    yesterday = today - timedelta(days=1)

    def _sum_for_day(day: date):
        start_dt = datetime.combine(day, datetime.min.time())
        end_dt = datetime.combine(day, datetime.max.time())
        q = (
            Bill.query.with_entities(func.coalesce(func.sum(Bill.total), 0.0))
            .filter(
                Bill.business_id == business_id,
                Bill.status == "COMPLETED",
                Bill.completed_at >= start_dt,
                Bill.completed_at <= end_dt,
            )
            .scalar()
        )
        return float(q or 0.0)

    # daily, weekly, monthly aggregates
    daily = calculate_daily_report(business_id, today)
    weekly_start = today - timedelta(days=6)
    monthly_start = today - timedelta(days=29)

    def _sum_range(start_date: date, end_date: date):
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        val = (
            Bill.query.with_entities(func.coalesce(func.sum(Bill.total), 0.0))
            .filter(
                Bill.business_id == business_id,
                Bill.status == "COMPLETED",
                Bill.completed_at >= start_dt,
                Bill.completed_at <= end_dt,
            )
            .scalar()
        )
        return float(val or 0.0)

    today_revenue = daily["total_sales"]
    yesterday_revenue = _sum_for_day(yesterday)
    this_week_revenue = _sum_range(weekly_start, today)
    last_week_revenue = _sum_range(weekly_start - timedelta(days=7), weekly_start - timedelta(days=1))
    this_month_revenue = _sum_range(monthly_start, today)
    last_month_revenue = _sum_range(monthly_start - timedelta(days=30), monthly_start - timedelta(days=1))

    # line chart: last 7 days revenue
    daily_points = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        daily_points.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "label": day.strftime("%d %b"),
                "revenue": _sum_for_day(day),
            }
        )

    # top products
    start_top, end_top = _range_for_days(30)
    top_rows = (
        BillItem.query.join(Bill, BillItem.bill_id == Bill.id)
        .with_entities(BillItem.product_name, func.sum(BillItem.quantity).label("qty"))
        .filter(
            Bill.business_id == business_id,
            Bill.status == "COMPLETED",
            Bill.completed_at >= start_top,
            Bill.completed_at <= end_top,
        )
        .group_by(BillItem.product_name)
        .order_by(func.sum(BillItem.quantity).desc())
        .limit(10)
        .all()
    )
    top_products = [{"name": r.product_name, "quantity": int(r.qty)} for r in top_rows]

    return {
        "daily": daily,
        "series": {
            "daily_revenue": daily_points,
            "top_products": top_products,
        },
        "comparisons": {
            "today_vs_yesterday": {
                "today": today_revenue,
                "yesterday": yesterday_revenue,
            },
            "week": {
                "this_week": this_week_revenue,
                "last_week": last_week_revenue,
            },
            "month": {
                "this_month": this_month_revenue,
                "last_month": last_month_revenue,
            },
        },
    }

