
from apps.home import blueprint
from apps.lead.models import *
from apps.order.models import *
from apps.product.models import *
from flask import render_template, request, redirect, url_for, flash, Markup, jsonify, abort, send_file, has_request_context, Response
from flask_login import login_required
from jinja2 import TemplateNotFound
import requests
from datetime import datetime, timedelta, date
from sqlalchemy import text, extract, func, or_
from apps import db, login_manager


@blueprint.route('/home')
@login_required
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("home/dashboard.html",segment='index')

@blueprint.route('/dashboard/stats')
def dashboard_stats():
    today = datetime.today()

    # --- จำนวนผู้สมัครเดือนนี้ / เดือนก่อน ---
    current_month_count = MemberModel.query.filter(
        func.date_trunc('month', MemberModel.created_at) == func.date_trunc('month', today)
    ).count()

    last_month = (today.replace(day=1) - timedelta(days=1))
    last_month_count = MemberModel.query.filter(
        func.date_trunc('month', MemberModel.created_at) == func.date_trunc('month', last_month)
    ).count()

    # --- สมาชิกที่ชำระเงินแล้ว / ยังไม่ชำระ ---
    # paid_subquery = (
    #     db.session.query(OrderModel.member_id)
    #     .join(PaymentModel)
    #     .filter(PaymentModel.amount > 0)
    #     .distinct()
    # ).subquery()

    # paid_members = db.session.query(func.count(MemberModel.id)).filter(MemberModel.id.in_(paid_subquery)).scalar()
    # unpaid_members = db.session.query(func.count(MemberModel.id)).filter(~MemberModel.id.in_(paid_subquery)).scalar()

    # payment_summary = {"paid": paid_members, "unpaid": unpaid_members}
    # total_members = MemberModel.query.count()
    # payment_summary["rate_percent"] = round((paid_members / total_members) * 100, 2) if total_members else 0
    # --- สมาชิกที่ชำระเงินแล้ว / ยังไม่ชำระ (รูปแบบใหม่แบบ GROUP BY) ---
    excluded = ["cancelled", "pending"]
    results = (
        db.session.query(
            MemberModel.id.label("member_id"),
            func.array_agg(OrderModel.status).label("statuses")
        )
        .outerjoin(OrderModel, OrderModel.member_id == MemberModel.id)
        .group_by(MemberModel.id)
        .all()
    )

    paid_members = 0
    unpaid_members = 0

    for member_id, statuses in results:
        if not statuses or all(s in excluded for s in statuses):
            if all(s == "pending" for s in statuses):
                unpaid_members += 1
        else:
            paid_members += 1

    total_members = MemberModel.query.count()

    payment_summary = {
        "paid": paid_members,
        "unpaid": unpaid_members,
        "rate_percent": round((paid_members / total_members) * 100, 2) if total_members else 0
    }

    # --- สถิติผู้สมัครแยกตามสินค้า ---
    # product_stats = db.session.query(
    #     ProductForSalesModel.name,
    #     func.count(LeadProgram.id)
    # ).join(LeadProgram, LeadProgram.product_id == ProductForSalesModel.id)\
    #  .group_by(ProductForSalesModel.name).all()
    # product_stats_data = [{"product": p, "count": c} for p, c in product_stats]

    product_stats = (
        db.session.query(
            ProductForSalesModel.name,
            func.count(func.distinct(OrderModel.member_id))
        )
        .join(OrderModel, OrderModel.product_id == ProductForSalesModel.id)
        .group_by(ProductForSalesModel.name)
        .order_by(ProductForSalesModel.name.asc())  # ✅ เรียง A → Z
        .all()
    )

    product_stats_data = [{"product": p, "count": c} for p, c in product_stats]


    # --- รายได้ตามสินค้า ---
    revenue_by_product = db.session.query(
        ProductForSalesModel.name,
        func.coalesce(func.sum(PaymentModel.amount),0)
    ).join(PaymentModel, PaymentModel.product_id == ProductForSalesModel.id)\
     .group_by(ProductForSalesModel.name).all()
    revenue_product_data = [{"product": p, "amount": float(a)} for p, a in revenue_by_product]

    # --- ข้อมูลติดต่อสมาชิก ---
    contacts = db.session.query(MemberModel.first_name, MemberModel.last_name, MemberModel.email, MemberModel.phone).all()
    contacts_data = [{"first_name": f, "last_name": l, "email": e, "phone": p} for f,l,e,p in contacts]

    # # --- กราฟแนวโน้ม 6 เดือนล่าสุด ---
    # member_monthly = []
    # revenue_monthly = []
    # for i in range(6,-1,-1):
    #     month_start = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
    #     count = MemberModel.query.filter(
    #         func.date_trunc('month', MemberModel.created_at) == func.date_trunc('month', month_start)
    #     ).count()
    #     revenue = db.session.query(func.coalesce(func.sum(PaymentModel.amount),0))\
    #         .filter(func.date_trunc('month', PaymentModel.payment_date) == func.date_trunc('month', month_start)).scalar()
    #     member_monthly.append({"month": month_start.month, "total": count})
    #     revenue_monthly.append({"month": month_start.month, "total": float(revenue)})
    current_year = today.year
    current_month = datetime.now().month

    member_monthly = []
    revenue_monthly = []

    for month in range(1, current_month + 1):
        count = MemberModel.query.filter(
            func.extract('year', MemberModel.created_at) == current_year,
            func.extract('month', MemberModel.created_at) == month
        ).count()

        revenue = db.session.query(
            func.coalesce(func.sum(PaymentModel.amount), 0)
        ).filter(
            func.extract('year', PaymentModel.payment_date) == current_year,
            func.extract('month', PaymentModel.payment_date) == month
        ).scalar()

        member_monthly.append({"month": month, "total": count})
        revenue_monthly.append({"month": month, "total": float(revenue)})
    # # --- Total revenue เดือนนี้ ---
    total_revenue = db.session.query(func.coalesce(func.sum(PaymentModel.amount),0))\
        .filter(func.date_trunc('month', PaymentModel.payment_date) == func.date_trunc('month', today))\
        .scalar()
    
        


    return jsonify({
        "current_month_count": current_month_count,
        "last_month_count": last_month_count,
        "payment_summary": payment_summary,
        "product_stats": product_stats_data,
        "revenue_by_product": revenue_product_data,
        "contacts": contacts_data,
        "total_revenue": float(total_revenue),
        "member_monthly": member_monthly,
        "revenue_monthly": revenue_monthly
    })


@blueprint.route('/dashboard/statsV1')
@login_required
def dashboard_statsv1():
    
    # ----- กำหนดปีปัจจุบัน -----
    today = date.today()
    current_year = today.year
    cur_month = today.month
    last_month = (today.replace(day=1) - timedelta(days=1)).month

    # -------------------------------
    # 1️⃣ แนวโน้มการสมัครรายเดือน (Member)
    # -------------------------------
    member_monthly = (
        db.session.query(
            extract('month', MemberModel.created_at).label("month"),
            func.count(MemberModel.id).label("total")
        )
        .filter(extract('year', MemberModel.created_at) == current_year)
        .group_by("month")
        .order_by("month")
        .all()
    )

    # จำนวนผู้สมัครเดือนนี้ vs เดือนก่อน
    current_month_count = (
        db.session.query(func.count(MemberModel.id))
        .filter(extract('month', MemberModel.created_at) == cur_month)
        .scalar()
    )
    last_month_count = (
        db.session.query(func.count(MemberModel.id))
        .filter(extract('month', MemberModel.created_at) == last_month)
        .scalar()
    )

    # -------------------------------
    # 2️⃣ รายได้รวมรายเดือน (Payment)
    # -------------------------------
    revenue_monthly = (
        db.session.query(
            extract('month', PaymentModel.payment_date).label('month'),
            func.sum(PaymentModel.amount).label('total')
        )
        .filter(extract('year', PaymentModel.payment_date) == current_year)
        .group_by("month")
        .order_by("month")
        .all()
    )

    # -------------------------------
    # 3️⃣ อัตราการชำระเงินครบตามกำหนด
    # -------------------------------
    orders = db.session.query(OrderModel).all()
    paid_count = 0
    unpaid_count = 0

    for o in orders:
        total_paid = sum([p.amount for p in o.payments])
        net_price = float(o.net_price or 0)
        if total_paid >= net_price and net_price > 0:
            paid_count += 1
        else:
            unpaid_count += 1

    payment_rate = round(paid_count / len(orders) * 100, 2) if orders else 0

    # -------------------------------
    # สรุป JSON ส่งกลับ
    # -------------------------------
    return jsonify({
        "member_monthly": [{"month": int(m), "total": t} for m, t in member_monthly],
        "current_month_count": current_month_count,
        "last_month_count": last_month_count,
        "revenue_monthly": [{"month": int(m), "total": float(t or 0)} for m, t in revenue_monthly],
        "payment_summary": {
            "paid": paid_count,
            "unpaid": unpaid_count,
            "rate_percent": payment_rate
        }
    })

@blueprint.route('/dashboard1')
@login_required
def dashboard1():
    now = datetime.now()

    count_this_month = (
        db.session.query(MemberModel)
        .filter(
            extract('year', MemberModel.created_at) == now.year,
            extract('month', MemberModel.created_at) == now.month
        )
        .count()
    )
    print("Count this month:", count_this_month)

    paid_members = (
        db.session.query(func.count(func.distinct(MemberModel.id)))
        .join(OrderModel, OrderModel.member_id == MemberModel.id)
        .join(PaymentModel, PaymentModel.order_id == OrderModel.id)
        .filter(PaymentModel.amount > 0)   # มีการชำระเงินจริง
        .scalar()
    )       
    print("Paid members:", paid_members)
    unpaid_members = (
        db.session.query(func.count(func.distinct(MemberModel.id)))
        .join(OrderModel, OrderModel.member_id == MemberModel.id)
        .outerjoin(PaymentModel, PaymentModel.order_id == OrderModel.id)
        .filter((PaymentModel.id == None) | (PaymentModel.amount == 0))
        .scalar()
    )
    print("Unpaid members:", unpaid_members)

    results_country = (
        db.session.query(
            CountryModel.name.label("country"),
            func.count(LeadProgram.id).label("total")
        )
        .join(leadModel, leadModel.id == LeadProgram.lead_id)
        .join(CountryModel, CountryModel.id == leadModel.country_id)
        .group_by(CountryModel.name)
        .order_by(func.count(LeadProgram.id).desc())
        .all()
    )
    print("Results by country:", results_country)

    total_received = (
        db.session.query(func.sum(PaymentModel.amount))
        .filter(func.extract('year', PaymentModel.payment_date) == now.year)
        .filter(func.extract('month', PaymentModel.payment_date) == now.month)
        .scalar()
    )

    total_received = float(total_received or 0)
    print("Total received this month:", total_received)

    results_product = (
        db.session.query(
            ProductForSalesModel.name.label("product"),
            func.sum(PaymentModel.amount).label("total")
        )
        .join(ProductForSalesModel, ProductForSalesModel.id == PaymentModel.product_id)
        .group_by(ProductForSalesModel.name)
        .order_by(func.sum(PaymentModel.amount).desc())
        .all()
    )
    print("Results by product:", results_product)

    return render_template('home/dashboard.html', segment='dashboard')


def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
