# Colofon Forms: AGPL source offer

The default `ghcr.io/jmurray2011/colofon` image does not contain PyMuPDF and is
distributed under the licenses of its individual components, with Colofon-authored code
under MIT.

The optional `ghcr.io/jmurray2011/colofon-form` image combines Colofon's form tooling
with PyMuPDF and MuPDF. That combined image is offered under **GNU AGPL version 3 only**.
When Colofon-authored code is distributed as part of this combined image, it is
additionally offered under AGPL-3.0-only; its separate MIT grant remains available.

## Corresponding source

For an image tagged `X.Y.Z`, the complete Colofon source and build scripts are at the
matching `vX.Y.Z` Git tag and GitHub release:

<https://github.com/jmurray2011/colofon/releases>

Each form-image release also attaches the exact `pymupdf-1.28.2.tar.gz` and
`mupdf-1.28.2-source.tar.gz` source archives corresponding to the bundled PyMuPDF and
MuPDF binaries. The release notes include their SHA-256 checksums. The authoritative
binary dependency hashes are in `tools/requirements-form-container.txt`, and the
reproducible build recipe is the `forms` target in `Dockerfile`.

The full AGPL-3.0 license text is installed in the image at
`/usr/share/licenses/colofon-form/AGPL-3.0.txt`. Source remains available for as long as
the corresponding image is offered. If an attachment becomes unavailable, report it
through the repository's issue tracker so equivalent access can be restored.

No commercial Artifex license is included with this distribution.
