# Third-party notices

Colofon-authored source code is licensed under the repository's MIT license. That license
does not replace the licenses of the following dependencies and redistributed assets.

- IBM Plex fonts under `engine/fonts/` are distributed under the SIL Open Font License
  1.1; the full text is in `engine/fonts/LICENSE.txt`.
- Packages under `packages/preview/` retain their upstream licenses in their respective
  package directories.
- Typst is distributed under Apache-2.0. The container installs its official release
  binary from <https://github.com/typst/typst>.
- veraPDF is offered under GPL-3.0-or-later or MPL-2.0-or-later. The container installs
  its official CLI distribution from <https://software.verapdf.org/>.
- The default `colofon` image does not contain PyMuPDF. The optional `colofon-form` image
  contains PyMuPDF and its embedded MuPDF components and is explicitly distributed under
  AGPL-3.0-only. See [AGPL-COMPLIANCE.md](AGPL-COMPLIANCE.md) for the license and
  corresponding-source offer.
- PyYAML is distributed under the MIT license.
- Eclipse Temurin, Python, Poppler, and Ubuntu runtime packages retain their upstream
  licenses. Their installed license and copyright material remains in the image, including
  Java notices under `$JAVA_HOME/legal` and package notices under `/usr/share/doc/`.

Both release images include an SBOM and provenance attestation in the OCI manifest. Those
records provide the authoritative component versions for a particular image digest.
This notice is informational and is not legal advice.
