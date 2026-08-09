"""The end-of-sub-game peer-visible semantic message families.

The frozen module boundary for finalization, established at Stage 4E-R7 ahead of
the families that will live here, so the next slice adds a family rather than an
architecture. Stage 4E-R6 froze that content as `NonceRevealEntry` and
`FinalNonceReveal` - one batched reveal per peer per sub-game, carrying the
`NonceValue` that `app.protocol_values` will own - and R6-FIX1/FIX2 froze their
exact contracts. **None of it is implemented yet**: that is a separate slice, and
a placeholder class here would be a semantic claim this module has not earned.
"""
