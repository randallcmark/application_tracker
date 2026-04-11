import argparse
from getpass import getpass

from app.auth.users import UserAlreadyExists, create_local_user
from app.db.session import SessionLocal


def create_admin(args: argparse.Namespace) -> int:
    password = args.password or getpass("Password: ")
    if not password:
        raise SystemExit("Password cannot be empty")

    with SessionLocal() as db:
        try:
            create_local_user(
                db,
                email=args.email,
                password=password,
                display_name=args.display_name,
                is_admin=True,
            )
        except UserAlreadyExists as exc:
            raise SystemExit(str(exc)) from exc
        db.commit()

    print(f"Created admin user: {args.email.strip().lower()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="application-tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    users_parser = subparsers.add_parser("users")
    users_subparsers = users_parser.add_subparsers(dest="users_command", required=True)

    create_admin_parser = users_subparsers.add_parser("create-admin")
    create_admin_parser.add_argument("--email", required=True)
    create_admin_parser.add_argument("--password")
    create_admin_parser.add_argument("--display-name")
    create_admin_parser.set_defaults(func=create_admin)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
