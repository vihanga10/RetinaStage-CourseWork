"""Grounded, deterministic explanations; no generated medical advice."""

LABELS = ("No DR", "Mild", "Moderate", "Severe", "Proliferative DR")


def review_rule(probabilities: list[float]) -> tuple[bool, list[str]]:
    ranked = sorted(range(5), key=lambda grade: probabilities[grade], reverse=True)
    top, second = ranked[:2]
    reasons = []
    if probabilities[top] < 0.70:
        reasons.append("Highest calibrated probability is below the illustrative 70% threshold")
    if probabilities[top] - probabilities[second] < 0.15 and abs(top - second) >= 2:
        reasons.append("Close top-two probabilities span at least two grades")
    return bool(reasons), reasons


def answer(question: str, result: dict) -> str:
    q = question.strip().lower()
    if not q or len(q) > 500:
        raise ValueError("Ask one question of up to 500 characters.")
    if any(word in q for word in ("treat", "medicine", "medication", "diagnos", "prescri", "cure", "should i take")):
        return ("I cannot diagnose or recommend treatment. A qualified clinician must "
                "interpret the image and decide any clinical next steps.")
    if any(word in q for word in ("heatmap", "grad-cam", "attention", "focus")):
        return ("The Grad-CAM overlay shows coarse processed-image regions associated "
                "with the selected output. It does not locate lesions, prove causality, "
                "or confirm that the grade is correct.")
    if any(word in q for word in ("blur", "robust", "stable", "sensitivity")):
        shift = result["blur_check"]
        return (f"With a fixed mild blur, the selected grade was Grade {shift['grade']} "
                f"({LABELS[shift['grade']]}). "
                f"The grade {'changed' if shift['changed'] else 'did not change'} in this "
                "single simulation. This is not external validation.")
    if any(word in q for word in ("review", "flag", "uncertain")):
        if result["review_required"]:
            return "Illustrative review flag: " + "; ".join(result["review_reasons"]) + "."
        return ("The illustrative confidence and top-two-gap rule did not trigger. "
                "That does not mean this result is clinically safe or correct.")
    if any(word in q for word in ("confidence", "probabilit", "percent")):
        values = ", ".join(
            f"Grade {i} {label}: {100 * result['probabilities'][i]:.1f}%"
            for i, label in enumerate(LABELS)
        )
        return (f"The calibrated model estimates are {values}. These are model "
                "estimates, not the probability that a clinical diagnosis is true.")
    return (f"The model selected Grade {result['grade']} "
            f"({LABELS[result['grade']]}) at {100 * result['confidence']:.1f}% "
            "calibrated confidence. This is a research output, not a diagnosis. "
            "You can ask about probabilities, review flags, the heatmap, or blur sensitivity.")
