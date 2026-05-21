from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Protocol


# Commands (intent)
@dataclass(frozen=True)
class OpenAccount:
    account_id: str
    owner: str


@dataclass(frozen=True)
class DepositMoney:
    account_id: str
    amount: int


@dataclass(frozen=True)
class WithdrawMoney:
    account_id: str
    amount: int


# Events (facts)
@dataclass(frozen=True)
class AccountOpened:
    account_id: str
    owner: str


@dataclass(frozen=True)
class MoneyDeposited:
    account_id: str
    amount: int


@dataclass(frozen=True)
class MoneyWithdrawn:
    account_id: str
    amount: int


class Event(Protocol):
    account_id: str


class EventStore:
    def __init__(self) -> None:
        self._events: List[Event] = []

    def append(self, event: Event) -> None:
        self._events.append(event)

    def load(self, account_id: str) -> Iterable[Event]:
        return [e for e in self._events if e.account_id == account_id]


class Account:
    def __init__(self, account_id: str) -> None:
        self.account_id = account_id
        self.owner = ""
        self.balance = 0

    @classmethod
    def from_events(cls, events: Iterable[Event]) -> "Account":
        account = cls(account_id="")
        for event in events:
            account.apply(event)
        return account

    def apply(self, event: Event) -> None:
        if isinstance(event, AccountOpened):
            self.account_id = event.account_id
            self.owner = event.owner
            self.balance = 0
        elif isinstance(event, MoneyDeposited):
            self.balance += event.amount
        elif isinstance(event, MoneyWithdrawn):
            self.balance -= event.amount

    def handle(self, command: object) -> List[Event]:
        if isinstance(command, OpenAccount):
            return [AccountOpened(command.account_id, command.owner)]
        if isinstance(command, DepositMoney):
            return [MoneyDeposited(command.account_id, command.amount)]
        if isinstance(command, WithdrawMoney):
            if command.amount > self.balance:
                raise ValueError("insufficient funds")
            return [MoneyWithdrawn(command.account_id, command.amount)]
        raise TypeError(f"unknown command: {command!r}")


class BalanceView:
    def __init__(self) -> None:
        self._balances: dict[str, int] = {}

    def apply(self, event: Event) -> None:
        if isinstance(event, AccountOpened):
            self._balances[event.account_id] = 0
        elif isinstance(event, MoneyDeposited):
            self._balances[event.account_id] += event.amount
        elif isinstance(event, MoneyWithdrawn):
            self._balances[event.account_id] -= event.amount

    def get(self, account_id: str) -> int:
        return self._balances.get(account_id, 0)


def main() -> None:
    store = EventStore()
    view = BalanceView()

    def run(command: object) -> None:
        history = store.load(command.account_id)  # type: ignore[attr-defined]
        account = Account.from_events(history)
        new_events = account.handle(command)
        for event in new_events:
            store.append(event)
            view.apply(event)

    run(OpenAccount("A-1", "Ada"))
    run(DepositMoney("A-1", 50))
    run(WithdrawMoney("A-1", 20))

    print("balance (read model):", view.get("A-1"))


if __name__ == "__main__":
    main()
