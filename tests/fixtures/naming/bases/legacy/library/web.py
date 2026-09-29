from .messages import MESSAGES
from .models import Book

# Routes and JSON fields are the contract with the mobile client.


def err2(code):
    return 409, {"error": MESSAGES[code]}


def handle_add_book(app, body):
    app.db.add_book(Book(body["isbn"], body["title"], body["author"], body.get("copies", 1)))
    return 201, {"isbn": body["isbn"]}


def handle_register(app, body):
    u = app.patrons.get_patron(body["user_id"], body.get("name", ""), body.get("email", ""))
    return 200, {"user_id": u.id, "fines": f"{u.fines_amt:.2f}"}


def handle_checkout(app, body):
    res = app.loans.process(body["user_id"], body["isbn"], app.today(), flag=body.get("staff", False))
    if not res["ok"]:
        return err2(res["reason"])
    loan = res["loan"]
    return 201, {"loan_id": loan.id, "due": loan.due.isoformat()}


def handle_return(app, body):
    fine = app.loans.do_return(body["loan_id"], app.today())
    if fine is None:
        return 404, {"error": MESSAGES["NOT_FOUND"]}
    return 200, {"fine": f"{fine:.2f}"}


def handle_reserve(app, body):
    res = app.loans.reserve(body["user_id"], body["isbn"], app.today())
    if not res["ok"]:
        return err2(res["reason"])
    return 201, {"hold_id": res["reservation"].id}


ROUTES = {
    ("POST", "/books"): handle_add_book,
    ("POST", "/members"): handle_register,
    ("POST", "/loans"): handle_checkout,
    ("POST", "/returns"): handle_return,
    ("POST", "/holds"): handle_reserve,
}


def dispatch(app, method, path, body):
    handler = ROUTES.get((method, path))
    if handler is None:
        return 404, {"error": "not found"}
    return handler(app, body)
