from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from st import State, batch, computed, effect, on_cleanup, readonly, scope, state, untrack, watch


@dataclass(frozen=True)
class CartLine:
    sku: str
    name: str
    unit_price: int
    quantity: int

    @property
    def subtotal(self) -> int:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class CartSummary:
    items: int
    subtotal: int
    discount: int
    shipping: int
    total: int


CATALOG = {
    "coffee": ("Coffee beans", 18_00),
    "filter": ("Paper filters", 6_00),
    "mug": ("Travel mug", 24_00),
}

INVENTORY = {
    "coffee": 20,
    "filter": 50,
    "mug": 8,
}


def money(cents: int) -> str:
    return f"${cents / 100:.2f}"


def format_summary(summary: CartSummary) -> str:
    return (
        f"{summary.items} items, subtotal {money(summary.subtotal)}, "
        f"discount {money(summary.discount)}, shipping {money(summary.shipping)}, "
        f"total {money(summary.total)}"
    )


cart: State[dict[str, CartLine]] = state({})
coupon_code: State[str] = state("")
customer_tier: State[str] = state("standard")

cart_view = readonly(cart)

item_count = computed(lambda: sum(line.quantity for line in cart.value.values()))
subtotal = computed(lambda: sum(line.subtotal for line in cart.value.values()))


def build_summary() -> CartSummary:
    lines = tuple(cart.value.values())
    items = sum(line.quantity for line in lines)
    subtotal_ = sum(line.subtotal for line in lines)
    coupon_discount = 10_00 if coupon_code.value == "WELCOME10" and subtotal_ >= 50_00 else 0
    member_discount = subtotal_ // 20 if customer_tier.value == "member" else 0
    discount = max(coupon_discount, member_discount)
    shipping = 0 if subtotal_ - discount >= 75_00 or items == 0 else 7_50

    return CartSummary(
        items=items,
        subtotal=subtotal_,
        discount=discount,
        shipping=shipping,
        total=max(subtotal_ - discount + shipping, 0),
    )


summary = computed(build_summary)

can_checkout = computed(
    lambda: item_count.value > 0
    and all(line.quantity <= INVENTORY.get(line.sku, 0) for line in cart.value.values())
)


def add_item(sku: str, quantity: int = 1) -> None:
    name, price = CATALOG[sku]
    current = cart.value
    line = current.get(sku, CartLine(sku, name, price, 0))
    cart.value = {
        **current,
        sku: replace(line, quantity=line.quantity + quantity),
    }


def remove_item(sku: str) -> None:
    cart.value = {key: line for key, line in cart.value.items() if key != sku}


def print_receipt() -> None:
    print("\nReceipt")
    for line in cart_view.value.values():
        print(f"- {line.name} x{line.quantity}: {money(line.subtotal)}")
    print(format_summary(summary.value))
    print(f"checkout enabled: {can_checkout.value}")


def main() -> None:
    with scope():
        effect(lambda: print(f"summary -> {format_summary(summary.value)}"))

        watch(
            lambda: can_checkout.value,
            lambda new, old: print(f"checkout changed: {old} -> {new}"),
            immediate=True,
        )

        def sync_coupon(new: str, old: str | None, on_cleanup: Callable[[Callable[[], None]], None]) -> None:
            if not new:
                return

            print(f"validating coupon {new!r}")
            on_cleanup(lambda: print(f"cancel coupon validation for {new!r}"))

        watch(lambda: coupon_code.value, sync_coupon)

        with batch():
            add_item("coffee", 2)
            add_item("filter")
            coupon_code.value = "WELCOME10"

        customer_tier.value = "member"
        add_item("mug", 10)
        remove_item("mug")

        with untrack():
            print(f"\nanalytics snapshot: {item_count.value} items, {money(subtotal.value)} before discounts")

        print_receipt()

        on_cleanup(lambda: print("\ncart session disposed"))


if __name__ == "__main__":
    main()
