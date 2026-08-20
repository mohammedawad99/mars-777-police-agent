"""Research-only police candidates. Never imported by tournament composition.

Every module here implements the same `StrategyPort` contract the production
policy does and reads the same lawful `Observation`, so a candidate is measured
on exactly the information the shipped agent has. Nothing here is promoted, and
a structural test holds that `composition.py` still selects the frozen
`CompetitiveStrategy`.
"""
