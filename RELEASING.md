# Releasing Colofon

Published tags are immutable. Never move or reuse a released tag; issue a new patch,
minor, or major version instead.

## Prepare

1. Choose a Semantic Versioning release number and update `CHANGELOG.md`.
2. If a versioned Typst package API changed, create its new version directory, update
   `typst.toml`, and update imports and examples. Do not rewrite an older package version.
3. Review pinned Typst and veraPDF versions and checksums, the Temurin digest, and both
   architecture hashes in `tools/requirements-container.txt` and
   `tools/requirements-form-container.txt`.
4. Confirm that public examples remain fictional, AI-generated, and free of private or
   organization-specific material.

## Verify

```sh
./tools/check.sh
python3 -m unittest discover -s tests -v
./build.sh
docker build --check .
docker build -t colofon:release .
docker run --rm colofon:release test
docker build --target forms -t colofon-form:release .
docker run --rm colofon-form:release test
```

Review the resulting diff, licenses, generated SBOM/provenance configuration, and the
container scan before release.

## Publish

1. Commit and push `main`; wait for CI to pass.
2. Create and push an annotated tag: `git tag -a vX.Y.Z -m "Colofon vX.Y.Z"`.
3. Wait for the tag workflow to test and publish both AMD64/ARM64 GHCR manifests.
4. Create the GitHub release from the existing tag using the changelog entry as notes.
   Attach the exact PyMuPDF and MuPDF source archives named in `AGPL-COMPLIANCE.md`.
5. Make both GHCR packages public. Verify anonymous pulls of
   `ghcr.io/jmurray2011/colofon:X.Y.Z` and
   `ghcr.io/jmurray2011/colofon-form:X.Y.Z`, and inspect both architectures.

If publishing fails after a tag is public, fix the problem and publish a new version.
Do not delete and recreate the original release tag.
