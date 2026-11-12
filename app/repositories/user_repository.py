from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ExpenseBook, User


class UserRepository:

    def get_by_id(self, db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, email: str):
        return db.query(User).filter(User.email == email.lower()).first()

    def get_by_username(self, db: Session, username: str):
        return db.query(User).filter(User.username == username.lower()).first()

    def get_by_login(self, db: Session, identifier: str):
        """Look up by email if the value contains "@", otherwise by username."""
        identifier = identifier.strip()
        if "@" in identifier:
            return self.get_by_email(db, identifier)
        return self.get_by_username(db, identifier)

    def set_password(self, db: Session, user: User, password_hash: str):
        user.password_hash = password_hash
        # Signs the user out everywhere: tokens issued before the reset stop working
        user.token_version = (user.token_version or 0) + 1
        db.commit()
        db.refresh(user)
        return user

    def revoke_tokens(self, db: Session, user: User):
        """Cancel every login token issued to this user so far."""
        user.token_version = (user.token_version or 0) + 1
        db.commit()
        db.refresh(user)
        return user

    def count(self, db: Session) -> int:
        return db.query(func.count(User.id)).scalar() or 0

    def create(
        self,
        db: Session,
        name: str,
        email: str,
        username: str,
        password_hash: str,
        claim_unowned_books: bool = False,
    ):
        user = User(name=name, email=email.lower(), username=username.lower(), password_hash=password_hash)
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
