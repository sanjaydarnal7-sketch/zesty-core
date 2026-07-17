from core.runtime.base_service import BaseService
from core.runtime.service_manager import ServiceManager


class DummyService(BaseService):
    def __init__(self):
        super().__init__("DummyService")

    def start(self):
        print("[DummyService] Started")

    def stop(self):
        print("[DummyService] Stopped")

    def health_check(self):
        return True


def main():
    manager = ServiceManager()

    dummy = DummyService()

    manager.register(dummy)

    print("\n=== STARTING SERVICES ===")
    manager.start_all()

    print("\n=== HEALTH REPORT ===")
    print(manager.health_report())

    print("\n=== STOPPING SERVICES ===")
    manager.stop_all()

    print("\n=== FINAL STATUS ===")
    print(manager.health_report())


if __name__ == "__main__":
    main()