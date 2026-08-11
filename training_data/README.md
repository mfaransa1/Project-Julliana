# Reviewed training examples

Only an explicitly approved, anonymized example belongs in `approved_examples.json`.

Each example must contain a valid existing intent `tag` and a short, non-sensitive
`pattern`. Never copy raw conversations, journal entries, contact details, or crisis
disclosures into this dataset. The trainer creates a candidate model only; promotion
requires evaluation and an explicit safety-test pass.

`english.json`, `kiswahili.json`, `sheng.json`, and `luo.json` contain small,
reviewed seed examples. Additions must use an existing intent tag and be reviewed
for safety, meaning, and dialect variation before training.
