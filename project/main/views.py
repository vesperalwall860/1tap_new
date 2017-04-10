import os, random, string

from calendar import month_abbr
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from flask import flash, render_template, redirect, request, url_for
from flask import jsonify, send_from_directory, session
from flask_login import current_user, login_user
from sqlalchemy import desc
from werkzeug.utils import secure_filename
from flask_mail import Message

from .services import MedicalDetailsService, MemberService, ClaimService
from .services import GuaranteeOfPaymentService, TerminalService
from .forms import ClaimForm, MemberForm, TerminalForm, GOPForm

from . import main
from .. import config, db, models, mail
from ..models import monthdelta, login_required

medical_details_service = MedicalDetailsService()
member_service = MemberService()
claim_service = ClaimService()
gop_service = GuaranteeOfPaymentService()
terminal_service = TerminalService()

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in config['production'].ALLOWED_EXTENSIONS

def pass_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def photo_file_name_santizer(photo):
    filename = secure_filename(photo.data.filename)

    if filename and allowed_file(filename):
        filename = str(random.randint(100000, 999999)) + filename
        photo.data.save(
            os.path.join(config['production'].UPLOAD_FOLDER, filename))

    if not filename:
        filename = ''

    if filename:
        photo_filename = '/static/uploads/' + filename
    else:
        photo_filename = '/static/img/person-solid.png'

    return photo_filename

def safe_div(dividend, divisor):
    try:
        result = dividend / divisor
    except ZeroDivisionError:
        result = 0.00
    return result

def percent_of(part, total):
    return safe_div(float(part), float(total)) * 100

def patients_amount(claims, _type):
    """Returns the in-patients for the given claims."""
    result = []

    for claim in claims:
        if claim.member.patient_type == _type:
            result.append(claim.member.id)

    result = list(set(result))

    return result


@main.route('/')
@login_required()
def index():
    if current_user.get_type() == 'provider':
        providers = []

    if current_user.get_type() == 'payer':
        claim_ids = [gop.claim.id for gop in current_user.payer.guarantees_of_payment if gop.claim]
        providers = models.Provider.query.join(models.Claim, models.Provider.claims)\
            .filter(models.Claim.id.in_(claim_ids)).all()

    if current_user.get_role() == 'admin':
        providers = models.Provider.query.all()

    members = member_service.all_for_user(current_user).all()

    claims_query = claim_service.all_for_user(current_user)\
                                .order_by(desc(models.Claim.datetime))
    claims = claims_query.all()
    total_claims = len(claims)

    # get the claims in the given month ranges
    months = ['0', '1', '3', '5', '6', '24']
    historical = {}
    for month in months:
        historical[month] = models.Claim.for_months(int(month))

    in_patients = {
        'total': len(patients_amount(claims, 'in')),
        '1_month': len(patients_amount(historical['1'][0], 'in')),
        '3_months': len(patients_amount(historical['3'][0], 'in')),
        '6_months': len(patients_amount(historical['6'][0], 'in')),
        '24_months': len(patients_amount(historical['24'][0], 'in'))
    }

    out_patients = {
        'total': len(patients_amount(claims, 'out')),
        '1_month': len(patients_amount(historical['1'][0], 'out')),
        '3_months': len(patients_amount(historical['3'][0], 'out')),
        '6_months': len(patients_amount(historical['6'][0], 'out')),
        '24_months': len(patients_amount(historical['24'][0], 'out'))
    }

    amount_summary = {
        'total': models.Claim.amount_sum(0)[0],
        '0': models.Claim.amount_sum(0),
        '1': models.Claim.amount_sum(1),
        '2': models.Claim.amount_sum(2),
        '3': models.Claim.amount_sum(3),
        '4': models.Claim.amount_sum(4),
        '5': models.Claim.amount_sum(5),
        '6': models.Claim.amount_sum(6),
        '24': models.Claim.amount_sum(24),
    }

    by_cost = {}
    by_icd = {}

    # calculate values for the Historical Claims section table
    for key, value in historical.items():
        for claim in value[0]:
            # calculate values for the Medical Summary By Cost table
            if not claim.amount in by_cost:
                by_cost[claim.amount] = {}

            if not key in by_cost[claim.amount]:
                by_cost[claim.amount][key] = 1
            else:
                by_cost[claim.amount][key] += 1

            # calculate values for the Medical Summary By ICD Code table
            if not claim.icd_code in by_icd:
                by_icd[claim.icd_code] = {}

            if not key in by_icd[claim.icd_code]:
                by_icd[claim.icd_code][key] = 1
            else:
                by_icd[claim.icd_code][key] += 1

    in_patients_perc = percent_of(in_patients['total'],
                            out_patients['total'] + in_patients['total'])

    out_patients_perc = percent_of(out_patients['total'],
                            out_patients['total'] + in_patients['total'])

    open_claims = claims_query.filter_by(status="Open").all()
    open_claims_perc = percent_of(len(open_claims), len(claims))

    closed_claims =  claims_query.filter_by(status="Closed").all()
    closed_claims_perc = percent_of(len(closed_claims), len(claims))

    amount_chart_data = {
        'labels': [],
        'values': []
    }
    # fill in the chart data for the 5 months
    for months in reversed(range(6)):
        month_name = month_abbr[monthdelta(datetime.now(), months * -1).month]
        amount_chart_data['labels'].append(month_name)
        amount_chart_data['values'].append(amount_summary[str(months)][2])

    in_patients_data = [
        len(patients_amount(historical['5'][0], 'in')),
        len(patients_amount(historical['3'][0], 'in')),
        len(patients_amount(historical['0'][0], 'in'))
    ]
    out_patients_data = [
        len(patients_amount(historical['5'][0], 'out')),
        len(patients_amount(historical['3'][0], 'out')),
        len(patients_amount(historical['0'][0], 'out'))
    ]

    pagination, claims = claim_service.prepare_pagination(claims_query)

    context = {
        'providers': providers,
        'members': members,
        'claims': claims,
        'pagination': pagination,
        'historical': historical,
        'out_patients': out_patients,
        'in_patients': in_patients,
        'amount_summary': amount_summary,
        'total_claims': total_claims,
        'by_cost': by_cost,
        'by_icd': by_icd,
        'in_patients_perc': in_patients_perc,
        'out_patients_perc': out_patients_perc,
        'open_claims':open_claims,
        'open_claims_perc':open_claims_perc,
        'closed_claims':closed_claims,
        'closed_claims_perc':closed_claims_perc,
        'in_patients_data': in_patients_data,
        'out_patients_data': out_patients_data,
        'today': datetime.now(),
        'amount_chart_data': amount_chart_data
    }

    return render_template('index.html', **context)


@main.route('/static/uploads/<filename>')
@login_required()
def block_unauthenticated_url(filename):
    return send_from_directory(os.path.join('static','uploads'),filename)


@main.route('/terminals')
@login_required(deny_types=['payer'])
def terminals():
    # retreive the all current user's terminals
    terminals = terminal_service.all_for_user(current_user)

    pagination, terminals = terminal_service.prepare_pagination(terminals)

    # render the "terminals.html" template with the given terminals
    return render_template('terminals.html', terminals=terminals,
                                             pagination=pagination)


@main.route('/terminal/<int:terminal_id>')
@login_required(deny_types=['payer'])
def terminal(terminal_id):
    terminal = terminal_service.get_for_user(terminal_id, current_user)

    claims = terminal.claims

    pagination, claims = claim_service.prepare_pagination(claims)

    # render the "terminal.html" template with the given terminal
    return render_template('terminal.html', terminal=terminal,
                                            claims=claims,
                                            pagination=pagination)


@main.route('/terminal/add', methods=['GET', 'POST'])
@login_required(types=['provider'])
def terminal_add():
    form = TerminalForm()

    # if the form was sent
    if form.validate_on_submit():
        terminal = models.Terminal(provider_id=current_user.provider.id)

        terminal_service.update_from_form(terminal, form)

        flash('The terminal has been added')
        return redirect(url_for('main.terminals'))

    return render_template('terminal-form.html', form=form)


@main.route('/terminal/<int:terminal_id>/edit', methods=['GET', 'POST'])
@login_required(types=['provider'])
def terminal_edit(terminal_id):
    # retreive the current user's terminal by its ID
    terminal = terminal_service.get_for_user(terminal_id, current_user)

    form = TerminalForm()

    # if the form was sent
    if form.validate_on_submit():
        terminal_service.update_from_form(terminal, form)

        flash('Data has been updated.')

     # if the form was just opened
    if request.method != 'POST':
        form.prepopulate(terminal)

    # render the "terminal-form.html" template with the given terminal
    return render_template('terminal-form.html', form=form, terminal=terminal)


@main.route('/claims')
@login_required()
def claims():
    claims = claim_service.all_for_user(current_user)

    # order by datetime
    claims = claims.order_by(desc(models.Claim.datetime))

    pagination, claims = claim_service.prepare_pagination(claims)

    # render the "claims.html" template with the given transactions
    return render_template('claims.html', claims=claims,
                                          pagination=pagination)


@main.route('/claim/<int:claim_id>', methods=['GET', 'POST'])
@login_required()
def claim(claim_id):
    claim = claim_service.get_for_user(claim_id, current_user)

    if claim.new_claim:
        claim.new_claim = 0
        db.session.add(claim)
        db.session.commit()

    form = GOPForm()

    form.payer.choices = [('0', 'None')]
    form.payer.choices += [(p.id, p.company) for p in \
                           current_user.provider.payers]

    form.icd_codes.choices = [(i.id, i.code) for i in \
        models.ICDCode.query.filter(models.ICDCode.code != 'None' and \
        models.ICDCode.code != '')]
    
    form.doctor_name.choices = [('0', 'None')]
    form.doctor_name.choices += [(d.id, d.name + ' (%s)' % d.doctor_type) \
                                for d in current_user.provider.doctors]

    if current_user.get_type() == 'provider' and request.method != 'POST':
        form.name.data = claim.member.name
        form.dob.data = claim.member.dob
        form.policy_number.data = claim.member.policy_number
        form.admission_date.data = claim.datetime
        form.admission_time.data = claim.datetime
        form.quotation.data = claim.amount
        form.gender.data = claim.member.gender
        form.national_id.data = claim.member.national_id
        form.current_national_id.data = claim.member.national_id
        form.tel.data = claim.member.tel

        form.medical_details_previously_admitted.data = datetime.now()

    if form.validate_on_submit():
        filename = photo_file_name_santizer(form.member_photo)

        member = models.Member.query.filter_by(
            national_id=form.national_id.data).first()

        if not member:
            member = models.Member(photo=photo_filename)

            member_service.update_from_form(member, form,
                                            exclude=['member_photo'])

        medical_details = medical_details_service.create(
            **{field.name.replace('medical_details_', ''): field.data \
               for field in form \
               if field.name.replace('medical_details_', '') \
               in medical_details_service.columns})

        payer = models.Payer.query.get(form.payer.data)

        gop = models.GuaranteeOfPayment()
        exclude = ['doctor_name', 'status']

        gop.claim = claim
        gop.payer = payer
        gop.member = member
        gop.provider = current_user.provider
        gop.doctor_name = models.Doctor.query.get(int(form.doctor_name.data)).name
        gop.status = 'pending'
        gop.medical_details = medical_details

        for icd_code_id in form.icd_codes.data:
            icd_code = models.ICDCode.query.get(int(icd_code_id))
            gop.icd_codes.append(icd_code)

        gop_service.update_from_form(gop, form, exclude=exclude)

        # initializing user and random password 
        user = None
        rand_pass = None
        
        # if the payer is registered as a user in our system
        if gop.payer.user:
            if gop.payer.pic_email:
                recipient_email = gop.payer.pic_email
            elif gop.payer.pic_alt_email:
                recipient_email = gop.payer.pic_alt_email
            else:
                recipient_email = gop.payer.user.email
            # getting payer id for sending notification    
            notification_payer_id = gop.payer.user.id
            
        # if no, we register him, set the random password and send
        # the access credentials to him
        else:
            recipient_email = gop.payer.pic_email
            rand_pass = pass_generator(size=8)
            user = models.User(email=gop.payer.pic_email,
                    password=rand_pass,
                    user_type='payer',
                    payer=gop.payer)
            db.session.add(user)
            # getting payer id for sending notification 
            notification_payer_id = user.id

        msg = Message("Request for GOP - %s" % gop.provider.company,
                      sender=("MediPay",
                              "request@app.medipayasia.com"),
                      recipients=[recipient_email])

        msg.html = render_template("request-email.html", gop=gop,
                                   root=request.url_root, user=user,
                                   rand_pass = rand_pass, gop_id=gop.id)

        # send the email
        try:
            mail.send(msg)
        except Exception as e:
            pass

        flash('Your GOP request has been sent.')

    if form:
        return render_template('claim.html', claim=claim, form=form)
    else:
        return render_template('claim.html', claim=claim)


@main.route('/claim/add', methods=['GET', 'POST'])
@login_required(types=['provider'])
def claim_add():
    terminals = terminal_service.all_for_user(current_user)
    members = member_service.all_for_user(current_user)

    form = ClaimForm()

    terminals_list = [(terminal.id,terminal.serial_number) \
                        for terminal in terminals]
    member_list = [(member.id,member.name) for member in members]

    form.terminal_id.choices += terminals_list
    form.member_id.choices += member_list

    # if the form was sent
    if form.validate_on_submit():
        claim = models.Claim(provider_id=current_user.provider.id)
        claim_service.update_from_form(claim, form)
        
        member = models.Member.query.get(form.member_id.data)

        flash('The claim has been added.')

        return redirect(url_for('main.claims'))

    return render_template('claim-form.html', form=form)


@main.route('/claim/<int:claim_id>/edit', methods=['GET', 'POST'])
@login_required(deny_types=['payer'])
def claim_edit(claim_id):
    claim = claim_service.get_for_user(claim_id, current_user)
    members = member_service.all_for_user(current_user)
    terminals = terminal_service.all_for_user(current_user)

    form = ClaimForm()

    terminal_list = [(terminal.id,terminal.serial_number) \
                        for terminal in terminals]
    member_list = [(member.id,member.name) for member in members]
    form.terminal_id.choices += terminal_list
    form.member_id.choices += member_list

    # if the form was sent
    if form.validate_on_submit():
        claim_service.update_from_form(claim, form)

        flash('Data has been updated')

     # if the form was just opened
    if request.method != 'POST':
        # fill in the form with the member's data
        exclude = ['datetime']
        form.prepopulate(model=claim, exclude=exclude)

        form.date.data = claim.datetime
        form.time.data = claim.datetime

    return render_template('claim-form.html', form=form, claim=claim)


@main.route('/members')
@login_required()
def members():
    members = member_service.all_for_user(current_user)

    pagination, members = member_service.prepare_pagination(members)

    # render the "members.html" template with the given members
    return render_template('members.html', members=members,
                                           pagination=pagination)


@main.route('/member/<int:member_id>')
@login_required()
def member(member_id):
    member = member_service.get_for_user(member_id, current_user)

    claims = member.claims

    pagination, claims = claim_service.prepare_pagination(claims)

    # render the "member.html" template with the given member
    return render_template('member.html', member=member, claims=claims,
                                          pagination=pagination)


@main.route('/member/add', methods=['GET', 'POST'])
@login_required(types=['provider'])
def member_add():
    form = MemberForm()

    # if the form was sent
    if form.validate_on_submit():
        # update the photo
        photo_filename = photo_file_name_santizer(form.photo)

        member = models.Member(photo=photo_filename)

        # append the patient to the provider
        # by which the patient has been created
        member.providers.append(current_user.provider)

        # save the form data to the object
        member_service.update_from_form(member, form, exclude=['photo'])

        return redirect(url_for('main.members'))

    return render_template('member-form.html', form=form)


@main.route('/member/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required(types=['provider'])
def member_edit(member_id):
    # retreive the current user's member by its ID
    member = member_service.get_for_user(member_id, current_user)

    form = MemberForm()

    if form.validate_on_submit():
        if form.photo.data:
            member.photo = photo_file_name_santizer(form.photo)

        member_service.update_from_form(member, form, exclude=['photo'])

        return redirect(url_for('main.member', member_id=member.id))

     # if the form was just opened
    if request.method != 'POST':
        form.marital_status.default = member.marital_status
        form.patient_type.default = member.patient_type
        form.gender.default = member.gender
        form.process()

        # fill in the form with the member's data
        exclude = ['marital_status', 'patient_type', 'gender']
        form.prepopulate(model=member, exclude=exclude)

    return render_template('member-form.html', form=form, member=member)


@main.route('/setup', methods=['GET', 'POST'])
@login_required()
def setup():
    return render_template('setup.html')


@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500


@main.route('/search', methods=['GET'])
def search():
    found = {
        'results': []
    }
    query = request.args.get('query')
    if not query or not current_user.is_authenticated:
        return jsonify(found)

    query = query.lower()

    claim_all = models.Claim.query.all()
    claim_current = []
    claim_current = claim_all

    for claim in claim_current:
        # initialazing location variable to put the claim's terminal data here,
        # if no terminal in a claim's object, it remains None
        location = None

        if claim.terminal:
            location = claim.terminal.location

        if query in str(claim.status).lower() \
        or query in str(claim.claim_number).lower() \
        or query in str(claim.claim_type).lower() \
        or query in str(claim.datetime) \
        or query in str(claim.admitted) \
        or query in str(claim.discharged) \
        or query in str(location).lower() \
        or query in str(claim.amount) :
            found['results'].append(claim.id)
            continue

    return jsonify(found)


@main.route('/icd-code/search', methods=['GET'])
def icd_code_search():
    found = []
    query = request.args.get('query')
    query = query.lower()
    
    if not query:
        return render_template('icd-code-search-results.html',
                               icd_codes=None, query=query)

    icd_codes = models.ICDCode.query.all()

    for icd_code in icd_codes:
        if query in icd_code.code.lower() \
        or query in icd_code.description.lower() \
        or query in icd_code.common_term.lower():
            found.append(icd_code)
            continue

    return render_template('icd-code-search-results.html', icd_codes=found,
                               query=query)