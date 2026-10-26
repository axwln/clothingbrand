# Category structure review — approved 2026-10-26

**Update:** The user approved this exact-label tree and the audit workbook as the import source. Local import is now implemented; see [current import and production instructions](../category-import.md). The proposal below is retained as review evidence.

Source: supplied `Devika_Clothings_Category_Audit.xlsx`. All three populated sheets were read. The original `DEVIKA CLOTHINGS.xlsx` is unavailable, so this is not an independent verification of its Working sheet. Audit suggestions are review evidence, not approved changes.

## Validation

- 108 copied rows with contiguous original row references 2–109.
- 29 distinct, case-sensitive source labels; review-sheet counts agree for every label.
- 24 copied rows have blank descriptions; all are preserved.
- Repeated rows, case, spelling, punctuation and description whitespace remain in source-rows.json.
- No SKU, price or stock data is provided; zero products proposed.

## Proposed tree

Every source label remains a distinct category with unchanged spelling. Proposed parent links are pending approval. Unknown labels stay top-level pending clarification; top-level placement does not constitute approval to publish them.

```text
SAREES
  SAREE WEAVING
  LINEN SAREE
  Saree printed
  Saree linen
  SAREE PRINTED A
  SAREE BAGALPURI
  SAREE BATIK(AD)
  Saree linen(E
  Saree plain
Jodhpuri Silk- Soft Cotton
Blouse.R.M
U.Skirt
Set Mundu
lining material
Lining Material
KURTHI
Churdhar.R.M
CHURIDAR MATERI
C.mg(G.S.Fancy w
CORD SET
TOP SET
Chundhar.R.M
CORDSET(O)
CHURIDHAR R M O
TOPSET(O)
KURTHI(O)
FROCK
Churidhar Material
```

## Full source-to-final mapping

| Original → proposed label (unchanged) | Parent | Source rows | Review note |
|---|---|---:|---|
| `SAREES` | Top-level | 24 | Keep literal label; descriptions are not subcategories or products. |
| `SAREE WEAVING` | `SAREES` | 3 | Proposed child only; client must confirm whether Weaving is a category or process. |
| `LINEN SAREE` | `SAREES` | 1 | Keep separate from Saree linen and Saree linen(E; no synonym merge approved. |
| `Saree printed` | `SAREES` | 2 | Keep separate from SAREE PRINTED A; A is unexplained. |
| `Saree linen` | `SAREES` | 2 | Keep separate from LINEN SAREE and Saree linen(E; no synonym merge approved. |
| `SAREE PRINTED A` | `SAREES` | 2 | A suffix unexplained; retain literal label. |
| `Jodhpuri Silk- Soft Cotton` | Top-level | 1 | Mixed material terms; leave top-level until category and placement are confirmed. |
| `Blouse.R.M` | Top-level | 5 | R.M unresolved. Front open, Vichithra, Elastic, Mirror, Sona Chandi remain descriptions. |
| `U.Skirt` | Top-level | 1 | Do not expand abbreviation from Saree Shape wear alone. |
| `SAREE BAGALPURI` | `SAREES` | 3 | Keep literal label; descriptions are not subcategories or products. |
| `SAREE BATIK(AD)` | `SAREES` | 1 | AD suffix unexplained; retain literal label. |
| `Saree linen(E` | `SAREES` | 1 | Incomplete suffix; retain exact spelling and separate identity. |
| `Set Mundu` | Top-level | 2 | Keep literal label; descriptions are not subcategories or products. |
| `Saree plain` | `SAREES` | 6 | Keep literal label; descriptions are not subcategories or products. |
| `lining material` | Top-level | 2 | Case variant of Lining Material; keep separate until merge approved. |
| `Lining Material` | Top-level | 3 | Keep separate from lining material until case-merge approval. |
| `KURTHI` | Top-level | 12 | Preserve spelling; do not rename Kurti automatically. |
| `Churdhar.R.M` | Top-level | 4 | R.M unresolved; keep separate from Chundhar.R.M and CHURIDHAR R M O. |
| `CHURIDAR MATERI` | Top-level | 1 | Truncated label; no merge with Churidhar Material approved. |
| `C.mg(G.S.Fancy w` | Top-level | 4 | Ambiguous/truncated abbreviation. Batik Print - 3 Pcs and Khadi Buti Print - 3 Pcs remain descriptions. |
| `CORD SET` | Top-level | 6 | Retain CORD SET; no automatic rename to Co-ords or merge with CORDSET(O). |
| `TOP SET` | Top-level | 6 | Keep literal label; descriptions are not subcategories or products. |
| `Chundhar.R.M` | Top-level | 1 | Potential spelling variant; no merge with Churdhar.R.M approved. |
| `CORDSET(O)` | Top-level | 1 | O suffix unresolved; keep separate from CORD SET. |
| `CHURIDHAR R M O` | Top-level | 2 | R M O unresolved; description 3 Pcs Cord Set does not establish category equivalence. |
| `TOPSET(O)` | Top-level | 2 | O suffix unresolved; keep separate from TOP SET. |
| `KURTHI(O)` | Top-level | 3 | O suffix unresolved; keep separate from KURTHI. |
| `FROCK` | Top-level | 1 | Keep literal label; descriptions are not subcategories or products. |
| `Churidhar Material` | Top-level | 6 | Preserve spelling and keep separate from CHURIDAR MATERI. |

## Description treatment

Column C remains raw evidence. Material/fabric terms (for example Chanderi Silk, Soft Cotton, Linen), printing/embellishment terms (Batik Print, Digital Print, Mirror), construction or set contents (Front open, 3 Pcs, Top Only), dimensions (Double -2.80mtr), and unclear names (Jaaviya, Ashika, Plady) are not promoted to product records or subcategories. Such classifications are provisional and do not replace original values.

## Existing site dependencies

The inspected local SQLite database has five active top-level categories: Sarees, Salwar Sets & Suits, Kurtis & Tops, Lehengas & Festive Wear, Accessories & More; each has three active products. There are no offer-category joins. This is a local snapshot, not a production audit. Preserve all five category records and their product foreign keys. The case variant Sarees versus source SAREES requires an explicit identity decision; do not automatically repurpose the existing row. Other demo products cannot be mapped from their current category labels alone. No existing category may be archived before product-level replacement mapping is confirmed.

The optional parent field and store migration 0002 already exist and are applied locally. Filters cover immediate children; no deeper hierarchy is proposed here. Navigation is database-driven but lacks hierarchy presentation, and homepage images still contain demo conditions.

## Required decisions before implementation

1. Approve the exact-label tree, or specify desired public display names and parent changes.
2. Resolve or explicitly defer ambiguous suffixes/abbreviations and any proposed case or synonym merges.
3. Confirm which unresolved labels may appear publicly; the preservation report alone does not approve publication.
4. Supply the original workbook for independent full-sheet verification, or explicitly authorize using this audit copy as the import authority.
5. Approve any treatment of the existing Sarees category and separately verify the 15 existing product assignments.

## Implementation and production plan after approval

Create a provenance-preserving, transactional category-only importer with --dry-run and collision checks. Preserve all copied rows, source label aliases and their approved category mapping; do not derive category identity from slug alone. Verify second-run idempotency and real navigation/filter counts with focused tests. Remove demo image conditions in favor of uploaded images and neutral fallbacks. Keep staff category management in the existing dashboard.

Before production changes, back up the persistent database, verify DATABASE_URL targets the same database as Vercel, and run the approved importer in dry-run mode against it. Apply only reviewed outstanding migrations via python manage.py migrate from a controlled environment with production database access; do not delete or regenerate existing migrations or run imports on each serverless request. Run the approved import command once, verify category counts/links and repeat its dry-run to confirm no additions. The final command syntax will be documented when implemented. No migration or import has been executed for this proposal.
