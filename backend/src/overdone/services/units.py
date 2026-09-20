LB_TO_KG = 0.45359237


def to_kg(value: float, unit: str) -> float:
    if unit == "kg":
        return value
    if unit == "lb":
        return value * LB_TO_KG
    raise ValueError(f"unsupported unit: {unit}")


def from_kg(weight_kg: float, unit: str) -> float:
    if unit == "kg":
        return weight_kg
    if unit == "lb":
        return weight_kg / LB_TO_KG
    raise ValueError(f"unsupported unit: {unit}")


def lb_to_kg(lb: float) -> float:
    return to_kg(lb, "lb")


def kg_to_lb(kg: float) -> float:
    return from_kg(kg, "lb")
