from __future__ import annotations

from src.models import Base
from src.deps import get_engine


def main():  # pragma: no cover - manual script
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("Tables created")


if __name__ == "__main__":  # pragma: no cover
    main()
