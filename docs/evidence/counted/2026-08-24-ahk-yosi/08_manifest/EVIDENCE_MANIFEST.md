# Evidence manifest — counted game MaRs-777 vs ahk-yosi, 2026-08-24

| | |
|---|---|
| `game_id` | `MaRs-777-vs-ahk-yosi` |
| `game_uid` | `5ed16f3b-4e6b-4e9d-65bf-8f5abab699f2` |
| opponent | `ahk-yosi` |
| MaRs-777 police | `feeee6542810d5a87eca001a4f9320ff0475b574` |
| MaRs-777 thief | `e49faa5184601037bdc4d872124c1e2ad8073c3b` |
| ahk-yosi | `093d55122d8e44ed20f9e0a69cd3f63d8eaed402` |
| official set | **1 of 14** — 6 config, 6 log, 1 result - no placeholder created |
| automatic reporting | **DID NOT SEND** |
| manual reporting | sent by operator; message_id UNKNOWN / not captured |
| fabricated values | **NONE** |

`LIVE_GAME` files were written by the running agents during the counted series.
`POST_GAME` files were written afterwards from that preserved evidence and are
documentation, never game output. No file was sanitized: an explicit
secret-value scan found no credential in any retained file.

| file | class | when | bytes | sha256 |
|---|---|---|---|---|
| `01_launch/launch_police.json` | RAW | LIVE_GAME | 3606 | `33b0df99e501eb96…` |
| `01_launch/launch_thief.json` | RAW | LIVE_GAME | 3606 | `33b0df99e501eb96…` |
| `01_launch/start_backends.sh` | RAW | LIVE_GAME | 1727 | `11f827d727bcb716…` |
| `01_launch/start_counted.sh` | RAW | LIVE_GAME | 4256 | `645bfb0f4ef1aec5…` |
| `02_protocol/declaration_MaRs-777-vs-ahk-yosi.json` | RAW | LIVE_GAME | 1330 | `ada8369ef25c7ea4…` |
| `03_subgames/friendly_MaRs-777-vs-ahk-yosi_police.json` | RAW | LIVE_GAME | 7902 | `b0962699e34f0cf5…` |
| `03_subgames/friendly_MaRs-777-vs-ahk-yosi_thief.json` | RAW | LIVE_GAME | 3805 | `ba98ec444eec5178…` |
| `04_runtime/gateway.log` | RAW | LIVE_GAME | 91864 | `796f1feee51c77b2…` |
| `04_runtime/police.log` | RAW | LIVE_GAME | 12028 | `f687231142990fcb…` |
| `04_runtime/thief.log` | RAW | LIVE_GAME | 8309 | `f63e7f539234aaf3…` |
| `05_result/MaRs-777_account_MaRs-777-vs-ahk-yosi.json` | DERIVED_SUMMARY | POST_GAME | 4456 | `a84778d732c77973…` |
| `06_reporting/REPORTING_RECORD.md` | DERIVED_SUMMARY | POST_GAME | 1724 | `2e33731cb19e14d2…` |
| `07_incident/INCIDENT_REPORT.md` | DERIVED_SUMMARY | POST_GAME | 5694 | `b7ce950e2825c26d…` |

Full digests are in `EVIDENCE_MANIFEST.json`.
