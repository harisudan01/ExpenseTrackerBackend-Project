from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ExpenseBook, User


class UserRepository:

    def get_by_id(self, db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, email: str):
        return db.query(User).filter(User.email == email.lower()).first()

    def count(self, db: Session) -> int:
        return db.query(func.count(User.id)).scalar() or 0

    def create(self, db: Session, name: str, email: str, password_hash: str, claim_unowned_books: bool = False):
        user = User(name=name, email=email.lower(), password_hash=password_hash)
        db.add(user)
        db.flush()  # assigns user.id without committing yet

        if claim_unowned_books:
            # Books created before accounts existed go to the first user, in the same transaction
            (
                db.query(ExpenseBook)
                .filter(ExpenseBook.user_id.is_(None))
                .update({ExpenseBook.user_id: user.id}, synchronize_session=False)
            )

        db.commit()
        db.refresh(user)
        return user
