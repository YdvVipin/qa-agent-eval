"""SystemAdapter — the interface every case study implements. core/ is written
only against this interface and never imports a specific system; that
separation is what makes 'the method generalizes' credible once more case
studies exist."""
from typing import Protocol, runtime_checkable


@runtime_checkable
class SystemAdapter(Protocol):
    def run(self, input: dict) -> dict:
        """Invoke the system under test with one input, return its raw output."""
        ...

    def expected_schema(self) -> dict:
        """Describe what a valid output looks like (field name -> expected type)."""
        ...

    def intent_of(self, output: dict) -> str | None:
        """Which agent/tool produced this output, if the system routes to specialists."""
        ...


def demo():
    class Conforms:
        def run(self, input):
            return {}

        def expected_schema(self):
            return {}

        def intent_of(self, output):
            return None

    class DoesNotConform:
        def run(self, input):
            return {}

    assert isinstance(Conforms(), SystemAdapter)
    assert not isinstance(DoesNotConform(), SystemAdapter)
    print("adapter.py self-check OK")


if __name__ == "__main__":
    demo()
