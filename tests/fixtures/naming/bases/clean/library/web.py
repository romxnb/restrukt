"""HTTP API of the mobile app.

Routes and JSON fields are the contract with the mobile client; the wire calls
the member id `user_id`. Each handler is named after its route.
"""

from .circulation import RefusalError
from .members import register_member
from .messages import LOAN_NOT_FOUND, REFUSAL_MESSAGES
from .models import Book

Response = tuple[int, dict]


def refused(error: RefusalError) -> Response:
    return 409, {"error": REFUSAL_MESSAGES[error.reason]}


def post_books(app, body: dict) -> Response:
    app.storage.add_book(Book(body["isbn"], body["title"], body["author"], body.get("copies", 1)))
    return 201, {"isbn": body["isbn"]}


def post_members(app, body: dict) -> Response:
    member = register_member(app.storage, body["user_id"], body.get("name", ""), body.get("email", ""))
    return 200, {"user_id": member.id, "fines": f"{member.unpaid_fines:.2f}"}


def post_loans(app, body: dict) -> Response:
    try:
        loan = app.circulation.lend(
            body["user_id"], body["isbn"], app.today(), ignore_holds=body.get("staff", False)
        )
    except RefusalError as error:
        return refused(error)
    return 201, {"loan_id": loan.id, "due": loan.due_on.isoformat()}


def post_returns(app, body: dict) -> Response:
    fine = app.circulation.return_book(body["loan_id"], app.today())
    if fine is None:
        return 404, {"error": LOAN_NOT_FOUND}
    return 200, {"fine": f"{fine:.2f}"}


def post_holds(app, body: dict) -> Response:
    try:
        hold = app.circulation.place_hold(body["user_id"], body["isbn"], app.today())
    except RefusalError as error:
        return refused(error)
    return 201, {"hold_id": hold.id}


ROUTES = {
    ("POST", "/books"): post_books,
    ("POST", "/members"): post_members,
    ("POST", "/loans"): post_loans,
    ("POST", "/returns"): post_returns,
    ("POST", "/holds"): post_holds,
}


def dispatch(app, method: str, path: str, body: dict) -> Response:
    handler = ROUTES.get((method, path))
    if handler is None:
        return 404, {"error": "not found"}
    return handler(app, body)
