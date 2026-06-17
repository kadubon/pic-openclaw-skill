# Publication Checklist

Before public release or registry submission, verify:

- root `SKILL.md` is present
- nested `skill/pic-residual-guard/SKILL.md` is present
- root and nested `SKILL.md` are synchronized
- no automatic PIC clone
- no automatic PIC install
- no `curl | bash` instructions in skill text
- no `Invoke-Expression` instructions in skill text
- no obfuscated code
- no credential collection
- no shell execution from action proposals
- no network by default
- `SECURITY.md` is present
- tests pass
- examples are sanitized
- license decision is explicit
- manual install is documented
- optional PIC-backed mode is clearly optional
