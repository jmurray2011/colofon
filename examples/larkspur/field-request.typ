// A fictional fillable form demonstrating the Larkspur house style.
#import "@local/house:0.1.0": *
#import "@local/larkspur-brand:0.1.0": theme as larkspur-theme

#show: form.with(
  title: "Field Session Request",
  subtitle: "Larkspur Field Station",
  logo: image(
    "/examples/larkspur/assets/larkspur-logo.svg",
    alt: "Larkspur Field Station logo",
  ),
  form-id: "LFS-OBS-01",
  intro: [This is a fictional, AI-generated example form. Names, organizations, systems, events, and data are not real. Submit one request for each observing session.],
  footer-note: [Fictional example form],
  theme: larkspur-theme,
)

= Requester

#field-block("Full name", "requester_name")
#grid(
  columns: (1fr, 1fr),
  column-gutter: 16pt,
  field-block("Email", "requester_email"),
  field-block("Organization", "requester_org"),
)

= Session

#grid(
  columns: (1fr, 1fr),
  column-gutter: 16pt,
  field-block("Requested date", "session_date"),
  field-block("Alternate date", "alternate_date"),
)

#field-block("Instrument or program", "program")

#block(breakable: false, below: 0.9em)[
  #flabel("Access needed")
  #v(4pt, weak: true)
  #box[
    #checkbox("access_deck", "Observing deck") #h(14pt)
    #checkbox("access_lab", "Instrument lab") #h(14pt)
    #checkbox("access_archive", "Data archive")
  ]
]

= Preparation

#field-block(
  "Safety or accessibility accommodations",
  "accommodations",
  lines: 3,
)
#field-block("Equipment and setup notes", "equipment_notes", lines: 4)

#block(breakable: false)[
  #checkbox(
    "rules_ack",
    "I have reviewed the station safety and lighting rules.",
  )
]
