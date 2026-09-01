// A form is authored in Typst (fillable fields need explicit placement), then made
// interactive with tools/make_form.py. See that script's header for the why.
#import "@local/house:0.1.0": *

#show: form.with(
  title: "Project Intake & Access Request",
  subtitle: "Acme -- new project onboarding",
  logo: image(
    "/tools/factory-examples/assets/example-logo.png",
    alt: "Acme logo",
  ),
  form-id: "ACME-INTK-04",
  intro: [Complete one form per project. Fields can be filled on screen or by hand.],
)

= Requester details

#field-block("Full name", "req_name")
#grid(
  columns: (1fr, 1fr),
  column-gutter: 16pt,
  field-block("Work email", "req_email"), field-block("Department", "req_dept"),
)

= Project

#field-block("Project name", "proj_name")

#block(breakable: false, below: 0.9em)[
  #flabel("Project type")
  #v(4pt, weak: true)
  #box[
    #checkbox("pt_proposal", "Proposal") #h(14pt)
    #checkbox("pt_report", "Report") #h(14pt)
    #checkbox("pt_other", "Other")
  ]
]

#field-block("Notes", "notes", lines: 3)
