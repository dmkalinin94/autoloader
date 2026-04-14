from product.logging_setup import configure_logging
from product.services.event_processor import EventProcessor


def main() -> int:
    logger = configure_logging()
    processor = EventProcessor(logger=logger)
    return processor.run_from_cli()


if __name__ == "__main__":
    raise SystemExit(main())
