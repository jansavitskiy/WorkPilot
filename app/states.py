from aiogram.fsm.state import State, StatesGroup



class Registration(StatesGroup):
    fullname = State()
    password1 = State()
    password2 = State()


class LoginState(StatesGroup):
    password = State()


class AdminPassword(StatesGroup):
    adpassword = State()


class Info(StatesGroup):
    org = State()
    hours = State()
    work = State()


class EditInfo(StatesGroup):
    edit_org = State()
    edit_hours = State()
    edit_work = State()


class DeleteConfirm(StatesGroup):
    confirm = State()


class Profile(StatesGroup):
    new_fio = State()


class AdminPanel(StatesGroup):
    report_days = State()


class OrgStates(StatesGroup):
    adding = State()
    deleting = State()


class OrganizationStates(StatesGroup):
    waiting_for_org_name = State()
