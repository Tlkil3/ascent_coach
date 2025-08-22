# 3) In the submit handler, right before calling OpenAI:
payload = build_founder_payload()
empty_blocks = list_empty_blocks(payload)

user_message = (
    "Founder Input (normalized JSON):\n"
    + str(payload)
    + "\n\nEMPTY_BLOCKS: " + str(empty_blocks)
    + "\n\nUse the response template exactly."
)

# 4) Change temperature to 0.0 and add STRICT_NO_INVENTION in messages:
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0.0,
    messages=[
        {"role": "system", "content": SINAPIS_COACH_SYS},
        {"role": "system", "content": MARKDOWN_INSTRUCTION},
        {"role": "system", "content": STRICT_NO_INVENTION},
        {"role": "system", "content": "Response Template:\n" + SINAPIS_RESPONSE_TEMPLATE},
        {"role": "user", "content": user_message},
    ],
)
