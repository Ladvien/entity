"""Demonstrate simple rollback logic using the new error classes.
Experimental example, not for production."""

from __future__ import annotations

from pipeline.errors import PluginContextError
from pipeline.stages import PipelineStage


class SimpleStateMachine:
    """Tiny state machine that can roll back when processing fails."""

    def __init__(self) -> None:
        self.state = "idle"
        self.history = []

    def transition(self, new_state: str) -> None:
        self.history.append(self.state)
        self.state = new_state
        print(f"-> {self.state}")

    def rollback(self) -> None:
        if self.history:
            self.state = self.history.pop()
            print(f"rollback to {self.state}")

    def do_work(self) -> None:
        raise PluginContextError(PipelineStage.DO, "Worker", "failure", {"step": 1})

    def run(self) -> None:
        try:
            self.transition("processing")
            self.do_work()
            self.transition("done")
        except PluginContextError as exc:
            print(f"caught: {exc}")
            self.rollback()
            self.transition("recovered")


if __name__ == "__main__":
    machine = SimpleStateMachine()
    machine.run()
    print(f"final: {machine.state}")
