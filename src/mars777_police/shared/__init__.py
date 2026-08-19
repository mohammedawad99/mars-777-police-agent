"""Cross-cutting authorities that every other layer may depend on.

The professional-software guideline's recommended tree puts version tracking and
other project-wide utilities here, below every layer and above none. Nothing in
this package may import a layer of ours: that is what makes it safe for `domain`,
`app`, `protocol`, `transport`, `infra` and the outer facade to share it.
"""
