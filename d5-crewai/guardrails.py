from typing import Any, Tuple
from crewai import TaskOutput


def validate_draft(output: TaskOutput) -> Tuple[bool, Any]:
    text = output.raw
    words = len(text.split())
    print(f"\n[guardrail] checking draft: {words} words")

    if not 250 <= words <= 350:
        return (False, f"Draft is {words} words. It must be between 250 and 350 words.")

    if "## Key Takeaways" not in text:
        return (False, "Draft is missing a '## Key Takeaways' section. Add it at the end with 3 bullet points.")

    print("[guardrail] PASSED")
    return (True, text)