"""
Builds eval/aquapilot_x3_manual.pdf - the test document for the DocuMind eval harness.

It is a FICTIONAL product manual (the product, company, figures and URLs are invented).
That is deliberate: no LLM has seen these facts during training, so a correct answer can only
come from retrieval. A famous public paper would let the model answer from memory and inflate scores.

Run:  python eval/make_test_pdf.py      (needs: pip install reportlab)
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

OUT = Path(__file__).resolve().parent / "aquapilot_x3_manual.pdf"

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=8, spaceAfter=4)
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=10, leading=14, spaceAfter=6)
NOTE = ParagraphStyle("N", parent=P, textColor=colors.HexColor("#444444"), fontName="Helvetica-Oblique")


def table(rows, widths):
    t = Table(rows, colWidths=[w * mm for w in widths])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


S = []
add = S.append

# --------------------------------------------------------------------------- cover
add(Paragraph("AquaPilot X3 Smart Irrigation Controller", ParagraphStyle("T", parent=H1, fontSize=22, leading=26)))
add(Paragraph("Product, Installation and Support Manual - Revision 4 (January 2026)", P))
add(Paragraph("Verdant Labs Pvt. Ltd.", P))
add(Spacer(1, 6))
add(Paragraph("This is a fictional document created to evaluate the DocuMind retrieval-augmented question "
              "answering system. The product, company, figures, standards claims and web addresses are invented.", NOTE))
add(Spacer(1, 10))
add(Paragraph("Contents", H2))
for line in ["1. Product overview", "2. Technical specifications", "3. Installation", "4. Connecting and pairing",
             "5. Watering programs and Smart Skip", "6. Water-savings study", "7. Error codes and troubleshooting",
             "8. Maintenance and firmware", "9. Developer API", "10. Subscription plans", "11. Warranty, returns and support",
             "12. Safety and compliance", "13. Firmware release history"]:
    add(Paragraph(line, P))
add(PageBreak())

# --------------------------------------------------------------------------- 1
add(Paragraph("1. Product overview", H1))
add(Paragraph(
    "The AquaPilot X3 is a Wi-Fi connected irrigation controller for homes, housing societies and small "
    "commercial landscapes. It replaces a conventional timer and decides each day whether, when and how long "
    "to water, using local weather forecasts, the soil type you select for each zone and the flow sensor reading. "
    "The X3 was launched in March 2025 and succeeds the AquaPilot X2, which supported only 8 zones.", P))
add(Paragraph(
    "Out of the box the X3 controls up to 16 watering zones. Capacity can be extended with ZX-16 expansion "
    "modules, each of which adds 16 zones. A maximum of two ZX-16 modules can be connected to one controller, "
    "giving a ceiling of 48 zones. Modules are connected with the supplied ribbon cable and are detected "
    "automatically at power-on.", P))
add(Paragraph(
    "The controller is managed from the AquaPilot mobile app or the web dashboard. All schedules are stored on "
    "the device itself, so watering continues as planned even if your internet connection drops. Weather data is "
    "refreshed from the Verdant forecast service every 3 hours.", P))
add(Paragraph(
    "Two hardware variants are sold. The outdoor model (X3-O) has a weather-sealed enclosure and a lockable "
    "cover. The indoor model (X3-I) is intended for garages and utility rooms and has a lighter enclosure. "
    "Apart from the enclosure, both variants are electrically identical and run the same firmware.", P))

# --------------------------------------------------------------------------- 2
add(Paragraph("2. Technical specifications", H1))
add(table([
    ["Parameter", "Value"],
    ["Zones", "16 built-in; up to 48 with two ZX-16 modules"],
    ["Power input", "24 VAC from the included plug-in transformer (230 V, 50 Hz input)"],
    ["Maximum output per zone", "0.65 A"],
    ["Maximum total output", "1.8 A across all active zones"],
    ["Simultaneous zones", "Up to 3 zones at once"],
    ["Wi-Fi", "2.4 GHz only, 802.11 b/g/n (5 GHz networks are not supported)"],
    ["Bluetooth", "Bluetooth Low Energy 5.2, used only during setup"],
    ["Operating temperature", "-10 C to 55 C"],
    ["Ingress protection", "IP56 (outdoor model X3-O); IP24 (indoor model X3-I)"],
    ["Dimensions", "190 x 140 x 42 mm"],
    ["Weight", "610 g (controller only)"],
    ["Schedule retention", "72 hours without power, using a supercapacitor (no battery)"],
    ["Sensor inputs", "1 flow sensor, 1 rain sensor or soil-moisture sensor"],
    ["Master valve / pump start", "Supported on terminal MV"],
], [55, 115]))
add(Spacer(1, 6))
add(Paragraph(
    "The X3 does not contain a battery. A supercapacitor keeps the clock and schedules for up to 72 hours during "
    "a power cut; after that the controller re-synchronises its clock over Wi-Fi when power returns.", P))
add(PageBreak())

# --------------------------------------------------------------------------- 3
add(Paragraph("3. Installation", H1))
add(Paragraph("3.1 Choosing a location", H2))
add(Paragraph(
    "Mount the controller on a vertical wall within reach of a 230 V socket for the transformer and within range "
    "of your Wi-Fi router. The bottom of the unit should be at least 1.2 metres above ground level to keep it clear "
    "of splashing water and garden equipment. Avoid direct afternoon sun on the display where possible. For the "
    "outdoor model, keep the cable entry facing downwards so that rain cannot run into the glands.", P))
add(Paragraph(
    "Do not install the controller, the transformer or any wiring junction within 3 metres of a swimming pool, "
    "pond or fountain.", P))
add(Paragraph("3.2 Wiring the valves", H2))
add(Paragraph(
    "Each valve needs one zone wire and a shared common wire. Use 18 AWG multi-core irrigation cable for runs of "
    "up to 240 metres between the controller and the furthest valve. For longer runs, use 16 AWG cable, which "
    "supports runs of up to 380 metres. Connect each zone wire to its numbered terminal and all common wires to the "
    "terminal marked C. If you use a master valve or pump-start relay, connect it to terminal MV.", P))
add(Paragraph(
    "After wiring, open the app and run the built-in Zone Test, which energises each zone for 2 minutes in turn and "
    "measures its current draw. Any zone drawing more than 0.8 A is flagged as a possible short circuit.", P))
add(Paragraph("3.3 Sensors", H2))
add(Paragraph(
    "A rain sensor or soil-moisture sensor connects to the S1 and S2 terminals. A pulse-type flow sensor connects to "
    "the F+ and F- terminals. During its first 14 days of operation the X3 learns the normal flow of each zone; "
    "after this learning period it can detect leaks and broken sprinkler heads.", P))

# --------------------------------------------------------------------------- 4
add(Paragraph("4. Connecting and pairing", H1))
add(Paragraph(
    "Install the AquaPilot app and create an account. To put the controller into pairing mode, press and hold the "
    "SET button for 5 seconds until the status LED pulses blue. The app finds the controller over Bluetooth and asks "
    "for the 6-digit setup code printed on the label inside the front cover. You then choose your Wi-Fi network; "
    "remember that only 2.4 GHz networks are supported.", P))
add(Paragraph(
    "If pairing fails three times in a row, the controller leaves pairing mode and the LED turns solid amber. Wait "
    "30 seconds and hold SET for 5 seconds again. To factory-reset the controller, hold SET and the MANUAL button "
    "together for 15 seconds; this erases all programs and Wi-Fi credentials.", P))
add(Paragraph(
    "Status LED colours: solid green means connected and idle; pulsing green means a zone is watering; "
    "pulsing blue means pairing mode; solid amber means not connected to Wi-Fi; flashing red means an active fault "
    "(see section 7).", P))
add(PageBreak())

# --------------------------------------------------------------------------- 5
add(Paragraph("5. Watering programs and Smart Skip", H1))
add(Paragraph("5.1 Programs", H2))
add(Paragraph(
    "A program is a set of zones, run times and start times. The X3 stores up to 12 programs, and each program can "
    "have up to 8 start times per day. Programs can run on selected weekdays, on odd or even dates, or every N days "
    "(from every 2 to every 30 days). If two programs overlap, the second one waits in a queue until the first "
    "finishes, unless parallel watering is enabled, in which case up to 3 zones may run at the same time.", P))
add(Paragraph("5.2 Smart Skip", H2))
add(Paragraph(
    "Smart Skip cancels a scheduled watering when rain is likely. By default, a watering is skipped if the forecast "
    "probability of rain within the next 24 hours is 60% or higher. The threshold can be adjusted in the app "
    "anywhere between 40% and 90%. Smart Skip also cancels watering if 6 mm or more of rain was recorded by your "
    "rain sensor in the previous 24 hours.", P))
add(Paragraph(
    "Freeze Skip prevents watering when the forecast temperature at the start time is below 3 C. Wind Skip, which "
    "is off by default, postpones watering when forecast wind speed exceeds 25 km/h.", P))
add(Paragraph("5.3 Seasonal Adjust and Cycle & Soak", H2))
add(Paragraph(
    "Seasonal Adjust scales all run times by a percentage between 10% and 200%, either manually or automatically "
    "from evapotranspiration data. Cycle & Soak splits a long run time into shorter cycles with soak periods in "
    "between, so that water soaks into clay or sloped soil instead of running off. The default soak period is "
    "20 minutes.", P))

# --------------------------------------------------------------------------- 6
add(Paragraph("6. Water-savings study", H1))
add(Paragraph(
    "Between June and December 2025, Verdant Labs ran a pilot with 312 homes in Pune. Each home's water use for "
    "irrigation was measured for eight weeks on its old timer and then for eight weeks on the AquaPilot X3 with Smart "
    "Skip and Seasonal Adjust enabled. Average outdoor water use fell by 31%. Homes with clay soil saw the largest "
    "reduction, 38%, largely because Cycle & Soak reduced runoff.", P))
add(Paragraph(
    "The study also found that 84% of participating households kept Smart Skip enabled at the default 60% threshold, "
    "and the median household received 11 skip notifications during the monsoon months.", P))
add(PageBreak())

# --------------------------------------------------------------------------- 7
add(Paragraph("7. Error codes and troubleshooting", H1))
add(Paragraph("When a fault is active the status LED flashes red and the app shows an error code.", P))
add(table([
    ["Code", "Meaning", "What to do"],
    ["E01", "Wi-Fi disconnected for more than 10 minutes", "Check the router; schedules keep running offline"],
    ["E04", "Clock not synchronised after a power cut longer than 72 hours", "Restore Wi-Fi so the clock can resync"],
    ["E07", "Zone short circuit (current above 0.8 A)", "Inspect the valve solenoid and wiring for that zone"],
    ["E12", "Flow anomaly: flow more than 25% above the learned baseline", "Look for a broken pipe or sprinkler head"],
    ["E15", "No flow detected while a zone is running", "Check the main water supply and the flow sensor"],
    ["E19", "Firmware update failed", "The controller retries automatically the next night"],
    ["E23", "Rain or soil sensor fault", "Check the S1/S2 wiring or disable the sensor in the app"],
], [16, 80, 74]))
add(Spacer(1, 6))
add(Paragraph(
    "If an E07 short circuit is detected, the affected zone is disabled and the rest of the program continues. "
    "The zone is re-enabled automatically after the next successful Zone Test.", P))
add(Paragraph(
    "If an E12 flow anomaly persists for 3 consecutive minutes, the controller closes the zone valve and, if "
    "configured, the master valve, and sends a push notification.", P))

# --------------------------------------------------------------------------- 8
add(Paragraph("8. Maintenance and firmware", H1))
add(Paragraph(
    "Firmware updates are downloaded automatically and installed at 02:00 local time, when watering is unlikely to "
    "be scheduled. If a watering program is running at 02:00, the update waits until it finishes. You can disable "
    "automatic updates in the app, but security updates are always installed.", P))
add(Paragraph(
    "Clean the inlet filter on the flow sensor every 6 months. For outdoor installations, check the cover seal once a "
    "year and replace it if it has cracked; replacement seals are part number VS-118. The controller itself needs no "
    "other routine maintenance.", P))
add(PageBreak())

# --------------------------------------------------------------------------- 9
add(Paragraph("9. Developer API", H1))
add(Paragraph(
    "Developers can control the X3 through a REST API. The base URL is https://api.aquapilot.example/v2 and all "
    "requests use HTTPS with JSON bodies. Authentication uses OAuth 2.0; access tokens expire after 3600 seconds and "
    "can be renewed with a refresh token, which is valid for 30 days.", P))
add(Paragraph(
    "The API is rate-limited to 60 requests per minute per controller. Requests above the limit receive HTTP status "
    "429 with a Retry-After header. Webhooks are available for the events zone_started, zone_finished, "
    "watering_skipped and fault_raised, and are retried up to 5 times with exponential backoff if your endpoint does "
    "not respond with a 2xx status.", P))
add(table([
    ["Endpoint", "Method", "Purpose"],
    ["/controllers", "GET", "List controllers on the account"],
    ["/controllers/{id}/zones/{n}/run", "POST", "Start a zone for a given number of minutes (1-120)"],
    ["/controllers/{id}/programs", "GET / PUT", "Read or replace watering programs"],
    ["/controllers/{id}/skip", "POST", "Skip all watering for 1 to 7 days"],
], [70, 25, 75]))

# --------------------------------------------------------------------------- 10
add(Paragraph("10. Subscription plans", H1))
add(Paragraph(
    "All core features, including Smart Skip and the mobile app, are free. The free plan supports one site (one "
    "physical location) with any number of controllers at that site.", P))
add(Paragraph(
    "AquaPilot Pro costs Rs 149 per month or Rs 1,499 per year. Pro adds a 7-day hyperlocal forecast, management of "
    "multiple sites from one account, water-use reports exportable as CSV, and an extended warranty (see section 11). "
    "A 30-day free trial of Pro is included with every new controller.", P))
add(PageBreak())

# --------------------------------------------------------------------------- 11
add(Paragraph("11. Warranty, returns and support", H1))
add(Paragraph(
    "The AquaPilot X3 has a 3-year limited warranty from the date of purchase, covering manufacturing defects. "
    "Customers with an active AquaPilot Pro subscription receive an extended warranty of 5 years in total. The "
    "warranty does not cover damage from lightning, flooding of the indoor model, or wiring faults outside the "
    "controller.", P))
add(Paragraph(
    "Unused products can be returned within 30 days of delivery for a full refund. For warranty claims, contact "
    "support to receive an RMA number; replacements are dispatched within 15 business days of receiving the faulty "
    "unit.", P))
add(Paragraph(
    "Customer support is available by phone and chat from 9:00 to 18:00 IST, Monday to Saturday, excluding national "
    "holidays. Support email requests are answered within 2 business days.", P))

# --------------------------------------------------------------------------- 12
add(Paragraph("12. Safety and compliance", H1))
add(Paragraph(
    "Use only the transformer supplied with the controller. Disconnect the transformer from the mains before wiring. "
    "The X3 is designed for 24 VAC irrigation valves only and must not be connected directly to mains-voltage pumps; "
    "use a pump-start relay on terminal MV instead.", P))
add(Paragraph(
    "The X3 is certified to BIS IS 13252 and carries CE marking for low-voltage equipment. It is not intended for "
    "controlling potable-water supply valves or fire-suppression systems.", P))

# --------------------------------------------------------------------------- 13
add(Paragraph("13. Firmware release history", H1))
add(table([
    ["Version", "Date", "Main changes"],
    ["3.0.0", "March 2025", "Launch firmware"],
    ["3.2.0", "May 2025", "Introduced Smart Skip and Freeze Skip"],
    ["3.4.1", "August 2025", "Added Cycle & Soak; fixed E04 clock-sync bug"],
    ["3.5.0", "January 2026", "Added Matter smart-home support and Wind Skip"],
], [25, 35, 110]))
add(Spacer(1, 6))
add(Paragraph(
    "Matter support, added in firmware 3.5.0, lets the X3 appear as a controllable device in compatible smart-home "
    "apps. Only manual zone start and stop are exposed over Matter; programs must still be edited in the AquaPilot app.",
    P))

add(PageBreak())
# --------------------------------------------------------------------------- Appendix A: legacy X2 (distractor facts)
add(Paragraph("Appendix A. AquaPilot X2 (legacy model) reference", H1))
add(Paragraph(
    "This appendix is kept for owners upgrading from the previous generation. The X2 is no longer sold. Its "
    "specifications differ from the X3 in several important ways, and X2 accessories are not compatible with the X3.", P))
add(table([
    ["Parameter", "AquaPilot X2 (legacy)"],
    ["Zones", "8 built-in; no expansion modules"],
    ["Maximum total output", "1.2 A"],
    ["Wi-Fi", "2.4 GHz, 802.11 b/g"],
    ["Ingress protection", "IP44"],
    ["Schedule retention", "24 hours, using a CR2032 coin battery"],
    ["Programs", "Up to 6 programs with 4 start times each"],
    ["Rain-skip threshold", "Fixed at 70%, not adjustable"],
    ["Warranty", "2 years"],
    ["Firmware", "2.x series; final release 2.9.3 (December 2024)"],
], [55, 115]))
add(Spacer(1, 6))
add(Paragraph(
    "X2 owners who move to the X3 can import their programs from the app: open Settings, choose Migrate from X2, and "
    "select the old controller. Zone names and run times are copied; start times beyond the X2 limit of 4 per program "
    "are not affected because the X3 supports 8.", P))
add(Paragraph(
    "The X2 developer API (v1) was retired on 31 March 2026. It allowed 20 requests per minute per controller and used "
    "API keys instead of OAuth. Integrations should move to the v2 API described in section 9.", P))

# --------------------------------------------------------------------------- Appendix B: city schedules
add(Paragraph("Appendix B. Recommended starting schedules by city", H1))
add(Paragraph(
    "These starting points are for lawns on loam soil with spray heads. Seasonal Adjust and Smart Skip will refine "
    "them automatically after the first two weeks. Figures are illustrative.", P))
add(table([
    ["City", "Summer run time (min/zone)", "Monsoon run time (min/zone)", "Watering days (summer)"],
    ["Pune", "18", "6", "Every 2 days"],
    ["Mumbai", "15", "0 (Smart Skip usually active)", "Every 2 days"],
    ["Bengaluru", "14", "5", "Every 3 days"],
    ["Hyderabad", "20", "7", "Every 2 days"],
    ["Chennai", "22", "9", "Daily"],
    ["Delhi", "24", "8", "Daily"],
    ["Jaipur", "26", "10", "Daily"],
    ["Ahmedabad", "25", "9", "Daily"],
    ["Kolkata", "16", "4", "Every 2 days"],
    ["Indore", "21", "7", "Every 2 days"],
], [35, 45, 50, 40]))
add(Spacer(1, 6))
add(Paragraph(
    "Drip zones generally need longer run times than spray zones because drip emitters deliver water slowly. As a "
    "rule of thumb, start drip zones at three times the spray run time shown above and adjust after observing soil "
    "moisture at a depth of about 10 cm.", P))
add(PageBreak())

# --------------------------------------------------------------------------- Appendix C: plant water needs
add(Paragraph("Appendix C. Plant water needs and soil types", H1))
add(Paragraph(
    "When you create a zone, the app asks for the plant type and soil type. These choices set the zone's crop "
    "coefficient and infiltration rate, which the X3 uses to calculate run times.", P))
add(table([
    ["Plant type", "Crop coefficient", "Typical root depth"],
    ["Cool-season lawn", "0.80", "15 cm"],
    ["Warm-season lawn", "0.60", "20 cm"],
    ["Shrubs", "0.50", "45 cm"],
    ["Vegetable garden", "0.85", "30 cm"],
    ["Fruit trees", "0.65", "90 cm"],
    ["Succulents and cacti", "0.25", "20 cm"],
], [60, 50, 60]))
add(Spacer(1, 6))
add(table([
    ["Soil type", "Infiltration rate", "Cycle & Soak recommended?"],
    ["Sand", "25 mm/hour", "No"],
    ["Loam", "12 mm/hour", "Only on slopes"],
    ["Clay", "4 mm/hour", "Yes"],
], [50, 50, 70]))
add(Spacer(1, 6))
add(Paragraph(
    "For clay soil the app enables Cycle & Soak automatically and limits each cycle to a maximum of 8 minutes for "
    "spray zones. On sandy soil, watering more often for shorter periods is usually better than long, infrequent runs.", P))

# --------------------------------------------------------------------------- Appendix D: FAQ
add(Paragraph("Appendix D. Frequently asked questions", H1))
faq = [
    ("Can I use the X3 without an internet connection?",
     "Yes. Programs run from the controller's memory. Without internet you lose Smart Skip, remote control and "
     "notifications, but manual and scheduled watering continue."),
    ("Does the X3 work with a 5 GHz-only router?",
     "No. The X3 needs a 2.4 GHz network. Most dual-band routers broadcast both bands; enable the 2.4 GHz band or create "
     "a separate 2.4 GHz network name."),
    ("How many people can control one X3?",
     "The owner can invite up to 10 additional users from the app. Invited users can be given Viewer, Operator or Admin "
     "roles."),
    ("Can I water a zone manually from the controller?",
     "Yes. Press MANUAL, choose the zone with the arrow keys, and press SET. Manual runs default to 10 minutes."),
    ("What happens to watering during a power cut?",
     "Watering stops while power is off. When power returns within 72 hours, the controller resumes the schedule from "
     "the next start time; missed waterings are not repeated."),
    ("Can the X3 control a borewell pump?",
     "Yes, through a pump-start relay connected to terminal MV. Never connect a mains-voltage pump directly to the "
     "controller."),
    ("Is my data shared with third parties?",
     "Verdant Labs does not sell personal data. Anonymised, aggregated water-use statistics may be used to improve "
     "watering algorithms."),
    ("Can I see how much water I saved?",
     "Yes, if a flow sensor is installed. The Insights tab shows estimated litres saved by Smart Skip each month. Pro "
     "users can export the data as CSV."),
    ("How long does a firmware update take?",
     "Typically 3 to 5 minutes. The status LED pulses white during the update. Do not unplug the controller while the "
     "LED is white."),
    ("Can I name my zones?",
     "Yes. Zone names can be up to 24 characters long and can include photos taken from the app."),
    ("Does Smart Skip use my rain sensor or the forecast?",
     "Both. It skips if the forecast rain probability meets your threshold, or if the rain sensor recorded 6 mm or more "
     "in the previous 24 hours."),
    ("What does a solid amber LED mean?",
     "The controller is not connected to Wi-Fi. Schedules still run. Check your router or re-enter Wi-Fi details from "
     "the app."),
]
for q, a in faq:
    add(Paragraph("<b>" + q + "</b> " + a, P))
add(PageBreak())

# --------------------------------------------------------------------------- Appendix E: glossary
add(Paragraph("Appendix E. Glossary", H1))
gloss = [
    ("Evapotranspiration (ET)", "The water lost from soil and plants through evaporation and transpiration, used by "
     "Seasonal Adjust to scale run times."),
    ("Crop coefficient", "A factor between 0 and 1 describing how much water a plant type needs relative to reference grass."),
    ("Master valve", "A valve upstream of all zone valves that opens whenever any zone runs, adding protection against leaks."),
    ("Pump-start relay", "A relay that lets the 24 VAC controller switch a mains-voltage pump safely."),
    ("Run time", "The number of minutes a zone is watered during one start time."),
    ("Soak period", "The pause between Cycle & Soak cycles that lets water infiltrate the soil."),
    ("Learned baseline", "The normal flow for a zone, learned during the first 14 days with a flow sensor."),
    ("Site", "A physical location such as a home or building. The free plan supports one site."),
    ("RMA", "Return Merchandise Authorisation, the reference number needed for a warranty replacement."),
    ("Matter", "An open smart-home standard supported by the X3 from firmware 3.5.0."),
]
for term, d in gloss:
    add(Paragraph("<b>" + term + ":</b> " + d, P))

# --------------------------------------------------------------------------- Appendix F: installer checklist
add(Paragraph("Appendix F. Installer checklist", H1))
for item in [
    "Confirm the site has a 2.4 GHz Wi-Fi signal of at least two bars at the mounting point.",
    "Mount the controller with its base at least 1.2 m above the ground and more than 3 m from any pool or pond.",
    "Use 18 AWG cable for runs up to 240 m, or 16 AWG for runs up to 380 m.",
    "Label every zone wire before connecting it to the terminal block.",
    "Run Zone Test and confirm that no zone draws more than 0.8 A.",
    "Pair the controller and confirm the status LED is solid green.",
    "Set plant and soil type for every zone, then enable Smart Skip.",
    "If a flow sensor is fitted, tell the owner that leak detection starts after the 14-day learning period.",
    "Hand over the setup code card and register the warranty in the app.",
]:
    add(Paragraph("- " + item, P))

SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                  topMargin=18 * mm, bottomMargin=18 * mm,
                  title="AquaPilot X3 Manual (fictional test document)").build(S)
print("wrote", OUT)
