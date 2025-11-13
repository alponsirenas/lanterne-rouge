"""Seed script to create admin and tester accounts."""
from sqlalchemy.orm import Session

from lanterne_rouge.backend.core.security import get_password_hash
from lanterne_rouge.backend.db.session import SessionLocal
from lanterne_rouge.backend.models.user import User


def seed_users():
    """Seed admin and tester users."""
    db: Session = SessionLocal()
    
    try:
        # Check if users already exist
        admin_exists = db.query(User).filter(User.email == "admin@lanterne-rouge.com").first()
        tester_exists = db.query(User).filter(User.email == "tester@lanterne-rouge.com").first()
        
        if not admin_exists:
            admin = User(
                email="admin@lanterne-rouge.com",
                hashed_password=get_password_hash("admin_password_123"),
                is_active=True,
                is_admin=True,
            )
            db.add(admin)
            print("✓ Created admin user: admin@lanterne-rouge.com (password: admin_password_123)")
        else:
            print("→ Admin user already exists")
        
        if not tester_exists:
            tester = User(
                email="tester@lanterne-rouge.com",
                hashed_password=get_password_hash("tester_password_123"),
                is_active=True,
                is_admin=False,
            )
            db.add(tester)
            print("✓ Created tester user: tester@lanterne-rouge.com (password: tester_password_123)")
        else:
            print("→ Tester user already exists")
        
        db.commit()
        print("\n✓ Database seeding completed successfully!")
        
    except Exception as e:
        print(f"✗ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
