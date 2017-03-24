import json, requests

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from flask import redirect, url_for
from flask_login import current_user, UserMixin
from functools import wraps
from sqlalchemy import extract
from sqlalchemy.orm import class_mapper, ColumnProperty
from sqlalchemy.sql import func
from werkzeug import check_password_hash, generate_password_hash

from . import db, login_manager

def login_required(roles=["any"], types=["any"]):
    """Overwritten login_required decorator,
    which includes roles checking"""
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
               return login_manager.unauthorized()
            urole = current_user.get_role()
            utype = current_user.get_type()
            if (urole not in roles and "any" not in roles) and \
               (utype not in types and "any" not in types):
                # return login_manager.unauthorized()
                return redirect(url_for('main.index'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

def to_float_or_zero(value):
    try:
        value = float(value)
    except (ValueError, TypeError):
        value = 0.0
    return value

class ColsMapMixin(object):
    def columns(self):
        """Return the actual columns of a SQLAlchemy-mapped object"""
        return [prop.key for prop in \
            class_mapper(self.__class__).iterate_properties \
            if isinstance(prop, ColumnProperty)]


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True, index=True)
    user_type = db.Column(db.String(20))
    role = db.Column(db.String(80))
    provider = db.relationship('Provider', uselist=False, backref='user')
    payer = db.relationship('Payer', uselist=False, backref='user')
    password_hash = db.Column(db.String(128))
    bad_logins = db.Column(db.Integer)
    last_attempt = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(128))
    api_key = db.Column(db.String(128))
    premium = db.Column(db.SmallInteger)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_role(self):
        return self.role

    def get_type(self):
        return self.user_type


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Patient(db.Model):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, unique=True, index=True)
    photo = db.Column(db.String(255))
    name = db.Column(db.String(50))
    dob = db.Column(db.Date, default=datetime.now())
    gender = db.Column(db.String(8))
    tel = db.Column(db.String(20))
    policy_number = db.Column(db.Integer)
    guarantees_of_payment = db.relationship('GuaranteeOfPayment',
                                            backref='patient', lazy='dynamic')


class Member(ColsMapMixin, db.Model):
    __tablename__ = 'member'
    id = db.Column(db.Integer, primary_key=True)
    photo = db.Column(db.String(255)) # url to the photo from '/uploads'
    name = db.Column(db.String(64))
    sex = db.Column(db.String(20))
    dob = db.Column(db.DateTime, default=datetime.now())
    telephone = db.Column(db.String(80))
    email = db.Column(db.String(64))
    address = db.Column(db.String(127))
    address_additional = db.Column(db.String(127))
    action = db.Column(db.String(80))
    marital_status = db.Column(db.String(40))
    start_date = db.Column(db.DateTime)
    effective_date = db.Column(db.DateTime)
    mature_date = db.Column(db.DateTime)
    exit_date = db.Column(db.DateTime)
    product = db.Column(db.String(255))
    plan = db.Column(db.String(127))
    client_policy_number = db.Column(db.Integer)
    client_id_number = db.Column(db.String(127))
    card_number = db.Column(db.String(127))
    plan_type = db.Column(db.String(80))
    remarks = db.Column(db.String(255))
    dependents = db.Column(db.String(127))
    sequence = db.Column(db.String(127))
    patient_type = db.Column(db.String(50))
    raiting = db.Column(db.String(50))
    device_uid = db.Column(db.String(127))
    claims = db.relationship('Claim', backref='member', lazy='dynamic')

    def age(self):
        difference_in_years = relativedelta(datetime.now(),
                                            self.dob).years
        return difference_in_years


custom_payers = db.Table('custom_payers',
    db.Column('payer_id', db.Integer, db.ForeignKey('payer.id')),
    db.Column('provider_id', db.Integer, db.ForeignKey('provider.id'))
)

custom_members = db.Table('custom_members',
    db.Column('member_id', db.Integer, db.ForeignKey('member.id')),
    db.Column('provider_id', db.Integer, db.ForeignKey('provider.id'))
)

custom_icd_codes = db.Table('custom_icd_codes',
    db.Column('guarantee_of_payment_id', db.Integer,
        db.ForeignKey('guarantee_of_payment.id')),
    db.Column('icd_code_id', db.Integer, db.ForeignKey('icd_code.id'))
)


class Provider(db.Model):
    __tablename__ = 'provider'
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(60))
    provider_type = db.Column(db.String(20))
    pic = db.Column(db.String(60))
    pic_email = db.Column(db.String(30))
    pic_alt_email = db.Column(db.String(30))
    tel = db.Column(db.String(20))
    country = db.Column(db.String(20))
    street_name = db.Column(db.String(40))
    street_number = db.Column(db.String(20))
    state = db.Column(db.String(20))
    postcode = db.Column(db.String(20))
    guarantees_of_payment = db.relationship('GuaranteeOfPayment',
                                            backref='provider', lazy='dynamic')
    billing_codes = db.relationship('BillingCode',
                                    backref='provider', lazy='dynamic')
    doctors = db.relationship('Doctor', backref='provider', lazy='dynamic')
    payers = db.relationship('Payer', secondary=custom_payers,
        backref=db.backref('providers', lazy='dynamic'))
    contracts = db.relationship('Contract', backref='provider', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    terminals = db.relationship('Terminal', backref='provider', lazy='dynamic')
    claims = db.relationship('Claim', backref='provider', lazy='dynamic')
    members = db.relationship('Member', secondary=custom_members,
        lazy='dynamic', backref=db.backref('providers', lazy='dynamic'))


class BillingCode(db.Model):
    __tablename__ = 'billing_code'
    id = db.Column(db.Integer, primary_key=True)
    room_and_board = db.Column(db.Float)
    doctor_visit_fee = db.Column(db.Float)
    doctor_consultation_fee = db.Column(db.Float)
    specialist_visit_fee = db.Column(db.Float)
    specialist_consultation_fee = db.Column(db.Float)
    medicines = db.Column(db.Float)
    administration_fee = db.Column(db.Float)
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))


class Doctor(db.Model):
    __tablename__ = 'doctor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    department = db.Column(db.String(60))
    doctor_type = db.Column(db.String(20))
    photo = db.Column(db.String(256))
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))


class Terminal(ColsMapMixin, db.Model):
    __tablename__ = 'terminal'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(40))
    serial_number = db.Column(db.String(80))
    model = db.Column(db.String(100))
    location = db.Column(db.String(100))
    version = db.Column(db.String(40))
    last_update = db.Column(db.DateTime)
    remarks = db.Column(db.String(100))
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))
    claims = db.relationship('Claim', backref='terminal', lazy='dynamic')


def monthdelta(date, delta):
    m, y = (date.month+delta) % 12, date.year + ((date.month)+delta-1) // 12
    if not m: m = 12
    d = min(date.day, [31,
        29 if y%4==0 and not y%400==0 else 28,31,30,31,30,31,31,30,31,30,31][m-1])
    return date.replace(day=d,month=m, year=y)

def date_months_ago(months):
    """Returns a datetime range as a difference between the current
    date and the given month"""
    return date.today() + relativedelta(months=months * -1)


class Claim(ColsMapMixin, db.Model):
    __tablename__ = 'claim'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(40))
    claim_number = db.Column(db.String(80))
    claim_type = db.Column(db.String(80))
    datetime = db.Column(db.DateTime)
    admitted = db.Column(db.String(40))
    discharged = db.Column(db.String(40))
    amount = db.Column(db.String(127))
    icd_code = db.Column(db.String(127))
    gop_id = db.Column(db.Integer, db.ForeignKey('guarantee_of_payment.id'))
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    terminal_id = db.Column(db.Integer, db.ForeignKey('terminal.id'))

    def update_medipay(self):
        # the function creates/updates a Medipay GOP request
        if not self.guarantee_of_payment:
            patient = Patient(
                name=self.member.name,
                dob=self.member.dob,
                policy_number=self.member.client_policy_number
            )
            gop = GuaranteeOfPayment(
                    provider=current_user.provider,
                    patient=patient,
                    patient_action_plan=self.member.action,
                    admission_date=datetime.now(),
                    admission_time=datetime.now(),
                    reason=self.member.plan_type,
                    status='draft',
                    patient_medical_no=self.member.card_number,
                    timestamp=datetime.now(),
                    quotation=self.amount,
                    room_price=0.0,
                    doctor_fee=0.0,
                    surgery_fee=0.0,
                    medication_fee=0.0,
                    claim=self
                )
        else:
            gop = self.guarantee_of_payment
            gop.patient = gop.patient
            gop.patient.name = self.member.name
            gop.patient.dob = self.member.dob
            gop.policy_number = self.member.client_policy_number
            gop.patient_action_plan = self.member.action
            admission_date = datetime.now()
            admission_time = datetime.now()
            reason = self.member.plan_type
            status = 'draft'
            patient_medical_no = self.member.card_number
            timestamp = datetime.now()
            quotation = self.amount

        db.session.add(gop)
        db.session.commit()

    @classmethod
    def for_months_filter(cls, query_object, months, _type='all'):
        # the filter returns a query within a given month
        # and for the whole range from today to that month

        # '_type' may be either 'all' or 'scalar'
        # by 'all' it returns an objects list
        # by 'scalar' it returns object's value summ

        # select records whose date is between
        # today and some month in the past
        for_range = query_object.filter(cls.datetime and \
            cls.datetime.between(date_months_ago(months), date.today()))

        # select records whose month and year 
        # coincide with the given date in the past
        ago = query_object.filter(cls.datetime and \
          extract('month', cls.datetime) == date_months_ago(months).month and \
          extract('year', cls.datetime) == date_months_ago(months).year)

        # if the type of a final operation is 'scalar'
        # it summarizes the given records' values
        if _type == 'scalar':
            return (for_range.scalar(), ago.scalar())

        # otherwise it just returns the list of given records
        return (for_range.all(), ago.all())

    @classmethod
    def for_months(cls, months):
        # returns a tuple of claims within a given month
        # and for the whole range from today to that month

        return cls.for_months_filter(cls.query, months)

    @classmethod
    def amount_sum(cls, months=0):
        # returns a tuple with a total amount, amount for the given
        # month ago and for the whole range from today to the given month

        # base query which uses the SQL function 'sum'
        query = db.session.query(func.sum(cls.amount))

        # concatenate the tuple of a total amount and month amounts
        return (query.scalar(),) + cls.for_months_filter(query, months,
                                                        _type='scalar')


class Contract(db.Model):
    __tablename__ = 'contract'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50))
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))
    payer_id = db.Column(db.Integer, db.ForeignKey('payer.id'))


class Payer(db.Model):
    __tablename__ = 'payer'
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(60))
    payer_type = db.Column(db.String(20))
    pic = db.Column(db.String(50))
    pic_email = db.Column(db.String(30))
    pic_alt_email = db.Column(db.String(30))
    tel = db.Column(db.String(20))
    country = db.Column(db.String(20))
    street_name = db.Column(db.String(40))
    street_number = db.Column(db.String(20))
    state = db.Column(db.String(20))
    postcode = db.Column(db.String(20))
    guarantees_of_payment = db.relationship('GuaranteeOfPayment',
                                            backref='payer', lazy='dynamic')
    contracts = db.relationship('Contract', backref='payer', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def contract(self, user=current_user):
        if user.user_type and user.user_type == 'provider':
            contract = self.contracts.filter_by(provider=user.provider).first()
            if contract:
                return contract
            else:
                contract = Contract(payer=self,
                                    provider=user.provider,
                                    number=None)
                db.session.add(contract)
                return contract
        else:
            return None


class GuaranteeOfPayment(db.Model):
    __tablename__ = 'guarantee_of_payment'
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'))
    payer_id = db.Column(db.Integer, db.ForeignKey('payer.id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    icd_codes = db.relationship('ICDCode', secondary=custom_icd_codes,
        backref=db.backref('guarantee_of_payments', lazy='dynamic'))
    patient_action_plan = db.Column(db.Text)
    admission_date = db.Column(db.DateTime, default=datetime.now())
    admission_time = db.Column(db.DateTime, default=datetime.now())
    reason = db.Column(db.String(40))
    doctor_name = db.Column(db.String(40))
    patient_medical_no = db.Column(db.Integer)
    room_type = db.Column(db.String(20))
    room_price = db.Column(db.Float, default=0.0)
    doctor_fee = db.Column(db.Float, default=0.0)
    surgery_fee = db.Column(db.Float, default=0.0)
    medication_fee = db.Column(db.Float, default=0.0)
    quotation = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='draft')
    state = db.Column(db.String(20))
    final = db.Column(db.SmallInteger)
    reason_decline = db.Column(db.String(127))
    reason_close = db.Column(db.String(127))
    stamp_author = db.Column(db.String(50))
    timestamp_edited = db.Column(db.DateTime, default=datetime.now())
    timestamp = db.Column(db.DateTime)
    medical_details = db.relationship('MedicalDetails', uselist=False,
                                      backref='guarantee_of_payment')
    claim = db.relationship('Claim', uselist=False,
                            backref='guarantee_of_payment')

    def turnaround_time(self):
        if not self.timestamp_edited:
            time_edited = datetime.now()
        else:
            time_edited = self.timestamp_edited
        time_created = self.timestamp
        
        diff = (time_edited - time_created).total_seconds()
        days = divmod(diff, 86400)
        hours = divmod(days[1], 3600)
        minutes = divmod(hours[1], 60)
        seconds = minutes[1]

        if days[0] > 0:
            output = '%d days %d hrs %d mins' % (days[0], hours[0], minutes[0])
        elif hours[0] > 0:
            output = '%d hrs %d mins' % (hours[0], minutes[0])
        else:
            output = '%d mins' % (minutes[0])
        
        return output


class MedicalDetails(db.Model):
    __tablename__ = 'medical_details'
    id = db.Column(db.Integer, primary_key=True)
    gop_id = db.Column(db.Integer, db.ForeignKey('guarantee_of_payment.id'))
    symptoms = db.Column(db.String(255))
    temperature = db.Column(db.String(10))
    heart_rate = db.Column(db.String(20))
    respiration = db.Column(db.String(40))
    blood_pressure = db.Column(db.String(20))
    physical_finding = db.Column(db.String(127))
    health_history = db.Column(db.Text)
    previously_admitted = db.Column(db.Date)
    diagnosis = db.Column(db.String(127))
    in_patient = db.Column(db.SmallInteger)
    test_results = db.Column(db.String(255))
    current_therapy = db.Column(db.String(127))
    treatment_plan = db.Column(db.Text)


class ICDCode(db.Model):
    __tablename__ = 'icd_code'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40))
    edc = db.Column(db.String(40))
    description = db.Column(db.String(80))
    common_term = db.Column(db.String(40))


class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    message = db.Column(db.String(127))