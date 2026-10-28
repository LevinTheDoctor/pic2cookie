// UI strings in English and German. Every text the page shows comes from here;
// `de` must have every key of `en` (TypeScript checks it).
//
// "{name}" is replaced by a parameter. A key with a "_one" twin uses that one when n is 1.
// Server warnings and errors arrive as {code, params, text}: "notice.<code>" translates them,
// unknown codes fall back to the server's English text.

import { createContext, useContext } from 'react'

const en = {
  'lang.label': 'Language',
  'header.github': 'GitHub',
  'header.privacy': 'Privacy',

  'product.label': 'Product',
  'product.cutter': 'Cookie cutter',
  'product.coaster': 'Coaster',

  'upload.hero': 'Turn a picture into a cookie cutter or coaster',
  'upload.drop': 'Drop a picture',
  'upload.orClick': 'or click to choose',
  'upload.makesCutter': '(makes a cookie cutter)',
  'upload.makesCoaster': '(makes a coaster)',
  'upload.types': 'SVG, PNG, JPG or WebP',
  'upload.notice':
    'Pictures you upload are stored on this server and can be seen by everyone using it. Please do not upload photos of people or anything personal.',

  'designs.title': 'Designs',
  'designs.empty': 'No saved designs yet.',
  'designs.failed': 'failed',
  'designs.generating': 'generating…',

  'design.name': 'Design name',
  'status.generating': 'Generating…',
  'status.ready': 'Ready',
  'action.duplicate': 'Duplicate',
  'action.delete': 'Delete',
  'action.confirmDelete': 'Click again to delete',
  'action.close': 'Close',

  'picture.title': 'Picture',
  'picture.hint': 'click a part to change its role',
  'picture.tracing': 'Tracing…',
  'picture.featureTitle': '{id}: {role} (click to change)',
  'picture.aria': 'Picture with roles',

  'role.outer': 'Outer blade',
  'role.hole': 'Hole (Inner blade)',
  'role.imprint': 'Imprint blade',
  'role.motif': 'Motif',
  'role.ignore': 'Ignored',
  'legend.cookie': 'Cookie',
  'legend.plate': 'Plate',

  'view.cutter': 'Cutter',
  'view.coaster': 'Coaster',
  'view.print': 'Print view',
  'view.cutting': 'Cutting view',
  'view.top': 'Top',
  'view.underside': 'Underside',
  'view.generating': 'Generating…',
  'view.loading3d': 'Loading 3D view…',
  'view.loadingModel': 'Loading model…',
  'view.loadError': 'Could not load the model ({status})',

  'estimate.title': 'Filament estimate',
  'estimate.filament': 'Filament',
  'estimate.length': 'Length',
  'estimate.cost': 'Cost',
  'estimate.size': 'Size',
  'estimate.perColour': 'Per colour',
  'estimate.generating': 'Generating…',
  'estimate.note': 'Printed nearly solid; your slicer may differ slightly.',
  'part.plate': 'Plate',
  'part.motif': 'Motif',

  'print.title': 'Print',
  'print.printer': 'Printer',
  'print.material': 'Material',
  'print.price': 'Price per kg',
  'print.pause':
    'The Bambu project pauses before the layer at {z} mm: put the coin into its slot, then resume. With STL or 3MF, add that pause in your slicer.',
  'print.ams': 'Two colours: the Plate prints from AMS slot 1, the Motif from slot 2.',

  'download.title': 'Download',
  'download.openBambu': 'Open in Bambu Studio',
  'download.bambu': 'Bambu project (.3mf)',
  'download.stl': 'STL',
  'download.stlZip': 'STL (zip)',
  'download.stlZipTitle': 'One STL per colour',
  'download.threemf': '3MF',
  'download.picture': 'Picture SVG',
  'download.roles': 'Roles SVG',
  'download.rolesTitle': 'For pic2cookie make',

  'settings.more': 'More settings',

  'cutter.title': 'Cutter',
  'cutter.size': 'Size (longest side)',
  'cutter.blade_height': 'Blade height',
  'cutter.blade_thickness': 'Blade thickness',
  'cutter.flange_width': 'Flange width',
  'cutter.flange_height': 'Flange height',
  'cutter.imprint_offset': 'Imprint offset',
  'cutter.imprint_thickness': 'Imprint thickness',
  'cutter.bridge_width': 'Bridge width',
  'cutter.min_hole': 'Smallest hole',
  'cutter.min_imprint': 'Smallest imprint',
  'cutter.support': 'Imprints held by',
  'cutter.bridges': 'Bridges',
  'cutter.plate': 'Back plate',

  'coaster.title': 'Coaster',
  'coaster.shape': 'Shape',
  'coaster.round': 'Round',
  'coaster.square': 'Square',
  'coaster.rounded': 'Rounded',
  'coaster.silhouette': 'Silhouette',
  'coaster.size': 'Size',
  'coaster.thickness': 'Thickness',
  'coaster.margin': 'Margin around the Motif',
  'coaster.corner_radius': 'Corner radius',
  'coaster.motif_scale': 'Motif size (share of the most that fits)',
  'coaster.motif': 'Motif',
  'coaster.inlay': 'Inlay',
  'coaster.raised': 'Raised',
  'coaster.engraved': 'Engraved',
  'coaster.invert': 'Invert Motif',
  'coaster.plate_colour': 'Plate colour (AMS slot 1)',
  'coaster.motif_colour': 'Motif colour (AMS slot 2)',
  'coaster.rim': 'Rim',
  'coaster.feet': 'Foot recesses',
  'coaster.opener': 'Bottle opener',
  'coaster.opener.none': 'None',
  'coaster.opener.coin': 'With a coin',
  'coaster.opener.plastic': 'Plastic only',
  'coaster.opener_side': 'Opener side',
  'coaster.left': 'Left',
  'coaster.top': 'Top',
  'coaster.bottom': 'Bottom',
  'coaster.right': 'Right',
  'coaster.coin': 'Coin',
  'coaster.coin.eur2': '2 €',
  'coaster.coin.eur1': '1 €',
  'coaster.coin.eur050': '50 ct',
  'coaster.coin.usd025': 'US quarter',
  'coaster.coin.custom': 'Other coin',
  'coaster.coin_diameter': 'Coin diameter',
  'coaster.coin_thickness': 'Coin thickness',
  'coaster.motif_depth': 'Motif depth / height',
  'coaster.min_line': 'Thinnest Motif line',
  'coaster.rim_width': 'Rim width',
  'coaster.rim_height': 'Rim height',
  'coaster.foot_diameter': 'Foot recess diameter',
  'coaster.foot_depth': 'Foot recess depth',
  'coaster.opener_thickness': 'Opener thickness',

  'trace.title': 'Tracing',
  'trace.hint': 'changing it resets clicked roles',
  'trace.ink': 'Ink',
  'trace.inkColour': 'Ink colour',
  'trace.colour': 'Colour',
  'trace.alpha': 'Opaque pixels',
  'trace.tolerance': 'Colour tolerance',
  'trace.smoothing': 'Smoothing',
  'trace.invert': 'Invert',

  'privacy.title': 'Privacy notice (GDPR)',
  'privacy.who': 'Who is responsible',
  'privacy.noOperator':
    'The operator of this instance has not entered their contact details yet (PIC2COOKIE_HOSTING__OPERATOR__*).',
  'privacy.what': 'What is stored, and why',
  'privacy.whatText':
    'When you upload a picture, this server stores the picture, the settings you choose and the files made from it (STL, 3MF, Bambu project). This is needed to make and show your cookie cutter or coaster (Art. 6 (1) (b) GDPR). There are no accounts: every saved design can be seen, changed and deleted by everyone who uses this instance. Please do not upload photos of people or other personal data.',
  'privacy.keptDays':
    'Designs are kept for {days} days after their last change, then deleted automatically, or until you delete them. The delete button removes a design and all its files.',
  'privacy.keptUntilDeleted':
    'Designs are kept until you delete them. The delete button removes a design and all its files.',
  'privacy.logs': 'Server logs',
  'privacy.logsText':
    'Like any web server, this one sees your IP address, the time and the address you requested. They are only used to run and secure the service (Art. 6 (1) (f) GDPR) and are not combined with other data.',
  'privacy.cookies': 'No cookies, no tracking',
  'privacy.cookiesText':
    'This site sets no cookies, uses no analytics or tracking and loads nothing from other servers. Your language choice is kept in your own browser only. “Open in Bambu Studio” only hands the file to the program on your own computer.',
  'privacy.rights': 'Your rights',
  'privacy.rightsText':
    'You can ask for access to, correction or deletion of your data, restriction of processing, data portability, and object to processing (Art. 15–21 GDPR). You can also complain to a data protection supervisory authority (Art. 77 GDPR).',
  'privacy.full': 'Full privacy policy',
  'privacy.openSource': 'Pic2Cookie is open source:',

  'error.generic': 'Something went wrong.',

  'notice.separate_shapes': 'The picture has {n} separate shapes; only the largest is used.',
  'notice.hole_narrow': 'Hole {id} is narrower than {mm} mm; the dough may not come out of it.',
  'notice.holes_became_imprints': '{n} holes narrower than {mm} mm became Imprint blades.',
  'notice.holes_became_imprints_one': '1 hole narrower than {mm} mm became an Imprint blade.',
  'notice.imprints_dropped': 'Dropped {n} imprints smaller than {mm} mm.',
  'notice.imprints_dropped_one': 'Dropped 1 imprint smaller than {mm} mm.',
  'notice.imprint_offset_too_big': 'The imprint offset leaves no Imprint blade above the Flange.',
  'notice.gaps_solid': 'Gaps narrower than {mm} mm between parts of the shape will print solid.',
  'notice.too_big_for_bed': 'At {width} × {depth} mm it does not fit the bed of the {printer}.',
  'notice.parts_far_apart': "The picture's parts are far apart; the Plate follows their outline loosely.",
  'notice.lines_widened': 'Widened {n} Motif lines thinner than {mm} mm.',
  'notice.lines_widened_one': 'Widened 1 Motif line thinner than {mm} mm.',
  'notice.motif_pieces_dropped': 'Dropped {n} Motif pieces smaller than {mm2} mm².',
  'notice.motif_pieces_dropped_one': 'Dropped 1 Motif piece smaller than {mm2} mm².',
  'notice.feet_no_room': 'The Plate is too small for Foot recesses.',
  'notice.feet_some': 'Only {n} Foot recesses fit on this Plate.',
  'notice.feet_some_one': 'Only 1 Foot recess fits on this Plate.',
  'notice.feet_too_deep': 'The Foot recesses are too deep for this Plate and were left out.',
  'notice.no_motif': 'No part of the picture is a Motif; the Coaster is a plain Plate.',
  'notice.opener_too_thin': 'The opener should be at least {mm} mm thick to cover the coin.',
  'notice.nothing_to_make': 'There is nothing in this picture to make anything from.',
  'notice.margin_too_big': 'The margin leaves no room for the Motif.',
  'notice.motif_too_deep': 'The Motif depth must be less than {max} mm on a {thickness} mm Plate.',
  'notice.unknown_printer': 'Unknown printer {printer}.',
  'notice.not_a_colour': 'Not a colour: {ink}',
  'notice.unsupported_image': 'Not a supported image (PNG, JPG or WebP).',
  'notice.no_ink': 'No Ink found; try another Ink colour, a higher tolerance or Invert.',
  'notice.svg_invalid': 'This is not a valid SVG.',
  'notice.svg_bad_role': 'Unknown data-role {role}.',
  'notice.svg_no_outer': 'A role-marked SVG needs an element with data-role="outer".',
  'notice.upload_too_large': 'The file is larger than {mb} MB.',
  'notice.upload_type': 'Upload an SVG, PNG, JPG or WebP picture.',
  'notice.upload_too_many_pixels': 'The picture is larger than {px} px.',
} as const

export type Key = keyof typeof en

const de: Record<Key, string> = {
  'lang.label': 'Sprache',
  'header.github': 'GitHub',
  'header.privacy': 'Datenschutz',

  'product.label': 'Produkt',
  'product.cutter': 'Ausstecher',
  'product.coaster': 'Untersetzer',

  'upload.hero': 'Aus einem Bild wird ein Ausstecher oder Untersetzer',
  'upload.drop': 'Bild hierher ziehen',
  'upload.orClick': 'oder klicken zum Auswählen',
  'upload.makesCutter': '(wird ein Ausstecher)',
  'upload.makesCoaster': '(wird ein Untersetzer)',
  'upload.types': 'SVG, PNG, JPG oder WebP',
  'upload.notice':
    'Hochgeladene Bilder werden auf diesem Server gespeichert und sind für alle sichtbar, die ihn nutzen. Bitte lade keine Fotos von Personen oder andere persönliche Inhalte hoch.',

  'designs.title': 'Entwürfe',
  'designs.empty': 'Noch keine gespeicherten Entwürfe.',
  'designs.failed': 'fehlgeschlagen',
  'designs.generating': 'wird erstellt…',

  'design.name': 'Name des Entwurfs',
  'status.generating': 'Wird erstellt…',
  'status.ready': 'Fertig',
  'action.duplicate': 'Duplizieren',
  'action.delete': 'Löschen',
  'action.confirmDelete': 'Zum Löschen nochmal klicken',
  'action.close': 'Schließen',

  'picture.title': 'Bild',
  'picture.hint': 'Teil anklicken, um seine Rolle zu ändern',
  'picture.tracing': 'Wird nachgezeichnet…',
  'picture.featureTitle': '{id}: {role} (zum Ändern klicken)',
  'picture.aria': 'Bild mit Rollen',

  'role.outer': 'Außenklinge',
  'role.hole': 'Loch (Innenklinge)',
  'role.imprint': 'Prägeklinge',
  'role.motif': 'Motiv',
  'role.ignore': 'Ignoriert',
  'legend.cookie': 'Keks',
  'legend.plate': 'Platte',

  'view.cutter': 'Ausstecher',
  'view.coaster': 'Untersetzer',
  'view.print': 'Druckansicht',
  'view.cutting': 'Ausstechansicht',
  'view.top': 'Oben',
  'view.underside': 'Unterseite',
  'view.generating': 'Wird erstellt…',
  'view.loading3d': '3D-Ansicht wird geladen…',
  'view.loadingModel': 'Modell wird geladen…',
  'view.loadError': 'Das Modell konnte nicht geladen werden ({status})',

  'estimate.title': 'Filamentbedarf',
  'estimate.filament': 'Filament',
  'estimate.length': 'Länge',
  'estimate.cost': 'Kosten',
  'estimate.size': 'Größe',
  'estimate.perColour': 'Pro Farbe',
  'estimate.generating': 'Wird erstellt…',
  'estimate.note': 'Fast massiv gedruckt; dein Slicer kann leicht abweichen.',
  'part.plate': 'Platte',
  'part.motif': 'Motiv',

  'print.title': 'Druck',
  'print.printer': 'Drucker',
  'print.material': 'Material',
  'print.price': 'Preis pro kg',
  'print.pause':
    'Das Bambu-Projekt pausiert vor der Schicht bei {z} mm: Münze in den Schlitz legen und fortsetzen. Bei STL oder 3MF die Pause im Slicer einfügen.',
  'print.ams': 'Zwei Farben: Die Platte kommt aus AMS-Slot 1, das Motiv aus Slot 2.',

  'download.title': 'Herunterladen',
  'download.openBambu': 'In Bambu Studio öffnen',
  'download.bambu': 'Bambu-Projekt (.3mf)',
  'download.stl': 'STL',
  'download.stlZip': 'STL (zip)',
  'download.stlZipTitle': 'Eine STL pro Farbe',
  'download.threemf': '3MF',
  'download.picture': 'Bild-SVG',
  'download.roles': 'Rollen-SVG',
  'download.rolesTitle': 'Für pic2cookie make',

  'settings.more': 'Weitere Einstellungen',

  'cutter.title': 'Ausstecher',
  'cutter.size': 'Größe (längste Seite)',
  'cutter.blade_height': 'Klingenhöhe',
  'cutter.blade_thickness': 'Klingenstärke',
  'cutter.flange_width': 'Flanschbreite',
  'cutter.flange_height': 'Flanschhöhe',
  'cutter.imprint_offset': 'Prägeklingen kürzer um',
  'cutter.imprint_thickness': 'Stärke der Prägeklingen',
  'cutter.bridge_width': 'Stegbreite',
  'cutter.min_hole': 'Kleinstes Loch',
  'cutter.min_imprint': 'Kleinste Prägung',
  'cutter.support': 'Prägeklingen gehalten von',
  'cutter.bridges': 'Stegen',
  'cutter.plate': 'Rückplatte',

  'coaster.title': 'Untersetzer',
  'coaster.shape': 'Form',
  'coaster.round': 'Rund',
  'coaster.square': 'Quadrat',
  'coaster.rounded': 'Abgerundet',
  'coaster.silhouette': 'Silhouette',
  'coaster.size': 'Größe',
  'coaster.thickness': 'Dicke',
  'coaster.margin': 'Abstand um das Motiv',
  'coaster.corner_radius': 'Eckenradius',
  'coaster.motif_scale': 'Motivgröße (Anteil an der größtmöglichen)',
  'coaster.motif': 'Motiv',
  'coaster.inlay': 'Eingelegt',
  'coaster.raised': 'Erhaben',
  'coaster.engraved': 'Graviert',
  'coaster.invert': 'Motiv umkehren',
  'coaster.plate_colour': 'Farbe der Platte (AMS-Slot 1)',
  'coaster.motif_colour': 'Farbe des Motivs (AMS-Slot 2)',
  'coaster.rim': 'Randleiste',
  'coaster.feet': 'Mulden für Füße',
  'coaster.opener': 'Flaschenöffner',
  'coaster.opener.none': 'Keiner',
  'coaster.opener.coin': 'Mit Münze',
  'coaster.opener.plastic': 'Nur Kunststoff',
  'coaster.opener_side': 'Seite des Öffners',
  'coaster.left': 'Links',
  'coaster.top': 'Oben',
  'coaster.bottom': 'Unten',
  'coaster.right': 'Rechts',
  'coaster.coin': 'Münze',
  'coaster.coin.eur2': '2 €',
  'coaster.coin.eur1': '1 €',
  'coaster.coin.eur050': '50 ct',
  'coaster.coin.usd025': 'US-Quarter',
  'coaster.coin.custom': 'Andere Münze',
  'coaster.coin_diameter': 'Durchmesser der Münze',
  'coaster.coin_thickness': 'Dicke der Münze',
  'coaster.motif_depth': 'Motivtiefe / -höhe',
  'coaster.min_line': 'Dünnste Motivlinie',
  'coaster.rim_width': 'Breite der Randleiste',
  'coaster.rim_height': 'Höhe der Randleiste',
  'coaster.foot_diameter': 'Durchmesser der Mulden',
  'coaster.foot_depth': 'Tiefe der Mulden',
  'coaster.opener_thickness': 'Dicke des Öffners',

  'trace.title': 'Nachzeichnen',
  'trace.hint': 'Änderungen setzen angeklickte Rollen zurück',
  'trace.ink': 'Zeichenfarbe',
  'trace.inkColour': 'Zeichenfarbe',
  'trace.colour': 'Farbe',
  'trace.alpha': 'Deckende Pixel',
  'trace.tolerance': 'Farbtoleranz',
  'trace.smoothing': 'Glättung',
  'trace.invert': 'Umkehren',

  'privacy.title': 'Datenschutzhinweis (DSGVO)',
  'privacy.who': 'Verantwortlich',
  'privacy.noOperator':
    'Der Betreiber dieser Instanz hat seine Kontaktdaten noch nicht eingetragen (PIC2COOKIE_HOSTING__OPERATOR__*).',
  'privacy.what': 'Was gespeichert wird und warum',
  'privacy.whatText':
    'Wenn du ein Bild hochlädst, speichert dieser Server das Bild, die gewählten Einstellungen und die daraus erzeugten Dateien (STL, 3MF, Bambu-Projekt). Das ist nötig, um deinen Ausstecher oder Untersetzer zu erstellen und anzuzeigen (Art. 6 Abs. 1 lit. b DSGVO). Es gibt keine Benutzerkonten: Jeder gespeicherte Entwurf kann von allen, die diese Instanz nutzen, angesehen, geändert und gelöscht werden. Bitte lade keine Fotos von Personen oder andere personenbezogene Daten hoch.',
  'privacy.keptDays':
    'Entwürfe werden {days} Tage nach ihrer letzten Änderung automatisch gelöscht, oder früher, wenn du sie löschst. Der Löschen-Knopf entfernt einen Entwurf mit allen Dateien.',
  'privacy.keptUntilDeleted':
    'Entwürfe bleiben gespeichert, bis du sie löschst. Der Löschen-Knopf entfernt einen Entwurf mit allen Dateien.',
  'privacy.logs': 'Server-Logs',
  'privacy.logsText':
    'Wie jeder Webserver sieht dieser deine IP-Adresse, die Uhrzeit und die aufgerufene Adresse. Diese Daten dienen nur dem Betrieb und der Sicherheit des Dienstes (Art. 6 Abs. 1 lit. f DSGVO) und werden nicht mit anderen Daten zusammengeführt.',
  'privacy.cookies': 'Keine Cookies, kein Tracking',
  'privacy.cookiesText':
    'Diese Seite setzt keine Cookies, nutzt keine Analyse- oder Tracking-Dienste und lädt nichts von fremden Servern. Deine Sprachwahl wird nur in deinem eigenen Browser gespeichert. „In Bambu Studio öffnen“ übergibt die Datei nur an das Programm auf deinem eigenen Computer.',
  'privacy.rights': 'Deine Rechte',
  'privacy.rightsText':
    'Du hast das Recht auf Auskunft, Berichtigung und Löschung deiner Daten, auf Einschränkung der Verarbeitung, auf Datenübertragbarkeit und auf Widerspruch gegen die Verarbeitung (Art. 15–21 DSGVO). Außerdem kannst du dich bei einer Datenschutz-Aufsichtsbehörde beschweren (Art. 77 DSGVO).',
  'privacy.full': 'Vollständige Datenschutzerklärung',
  'privacy.openSource': 'Pic2Cookie ist Open Source:',

  'error.generic': 'Da ist etwas schiefgegangen.',

  'notice.separate_shapes': 'Das Bild hat {n} getrennte Formen; nur die größte wird verwendet.',
  'notice.hole_narrow': 'Loch {id} ist schmaler als {mm} mm; der Teig geht dort eventuell nicht heraus.',
  'notice.holes_became_imprints': '{n} Löcher schmaler als {mm} mm wurden zu Prägeklingen.',
  'notice.holes_became_imprints_one': '1 Loch schmaler als {mm} mm wurde zur Prägeklinge.',
  'notice.imprints_dropped': '{n} Prägungen kleiner als {mm} mm wurden weggelassen.',
  'notice.imprints_dropped_one': '1 Prägung kleiner als {mm} mm wurde weggelassen.',
  'notice.imprint_offset_too_big': 'Bei diesem Versatz bleibt über dem Flansch keine Prägeklinge übrig.',
  'notice.gaps_solid': 'Lücken schmaler als {mm} mm zwischen Teilen der Form werden massiv gedruckt.',
  'notice.too_big_for_bed': 'Mit {width} × {depth} mm passt es nicht auf das Druckbett des {printer}.',
  'notice.parts_far_apart': 'Die Teile des Bildes liegen weit auseinander; die Platte folgt ihrem Umriss nur grob.',
  'notice.lines_widened': '{n} Motivlinien dünner als {mm} mm wurden verbreitert.',
  'notice.lines_widened_one': '1 Motivlinie dünner als {mm} mm wurde verbreitert.',
  'notice.motif_pieces_dropped': '{n} Motivteile kleiner als {mm2} mm² wurden weggelassen.',
  'notice.motif_pieces_dropped_one': '1 Motivteil kleiner als {mm2} mm² wurde weggelassen.',
  'notice.feet_no_room': 'Die Platte ist zu klein für Mulden für Füße.',
  'notice.feet_some': 'Nur {n} Mulden für Füße passen auf diese Platte.',
  'notice.feet_some_one': 'Nur 1 Mulde für Füße passt auf diese Platte.',
  'notice.feet_too_deep': 'Die Mulden für Füße sind zu tief für diese Platte und wurden weggelassen.',
  'notice.no_motif': 'Kein Teil des Bildes ist Motiv; der Untersetzer ist eine schlichte Platte.',
  'notice.opener_too_thin': 'Der Öffner sollte mindestens {mm} mm dick sein, damit die Münze bedeckt ist.',
  'notice.nothing_to_make': 'Aus diesem Bild lässt sich nichts erstellen.',
  'notice.margin_too_big': 'Der Abstand lässt keinen Platz für das Motiv.',
  'notice.motif_too_deep': 'Bei einer {thickness} mm dicken Platte muss die Motivtiefe kleiner als {max} mm sein.',
  'notice.unknown_printer': 'Unbekannter Drucker {printer}.',
  'notice.not_a_colour': 'Keine Farbe: {ink}',
  'notice.unsupported_image': 'Kein unterstütztes Bild (PNG, JPG oder WebP).',
  'notice.no_ink': 'Keine Zeichenfarbe gefunden; versuche eine andere Farbe, eine höhere Toleranz oder Umkehren.',
  'notice.svg_invalid': 'Das ist kein gültiges SVG.',
  'notice.svg_bad_role': 'Unbekannte data-role {role}.',
  'notice.svg_no_outer': 'Ein SVG mit Rollen braucht ein Element mit data-role="outer".',
  'notice.upload_too_large': 'Die Datei ist größer als {mb} MB.',
  'notice.upload_type': 'Lade ein SVG-, PNG-, JPG- oder WebP-Bild hoch.',
  'notice.upload_too_many_pixels': 'Das Bild ist größer als {px} px.',
}

export type Lang = 'en' | 'de'
export const LANGS: [Lang, string][] = [
  ['en', 'EN'],
  ['de', 'DE'],
]
const DICTS: Record<Lang, Record<Key, string>> = { en, de }
export const STORAGE_KEY = 'pic2cookie.lang'

/** A warning or error from the server. */
export interface Notice {
  code: string
  params: Record<string, number | string>
  text: string
}

type Params = Record<string, number | string | null | undefined>

export interface I18n {
  lang: Lang
  setLang: (lang: Lang) => void
  /** A UI string. */
  t: (key: Key, params?: Params) => string
  /** A server warning or error, or a plain message. */
  tm: (notice: Notice | string) => string
  /** A number in the language's format (1.5 / 1,5). */
  num: (n: number) => string
}

export function initialLang(): Lang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'en' || saved === 'de') return saved
  } catch {
    // storage blocked: fall back to the browser's language
  }
  return typeof navigator !== 'undefined' && navigator.language?.toLowerCase().startsWith('de') ? 'de' : 'en'
}

function format(template: string, params: Params, num: (n: number) => string): string {
  return template.replace(/\{(\w+)\}/g, (match, name) => {
    const value = params[name]
    if (value === undefined || value === null) return match
    return typeof value === 'number' ? num(value) : value
  })
}

export function translator(lang: Lang, setLang: (lang: Lang) => void): I18n {
  const dict = DICTS[lang]
  const numberFormat = new Intl.NumberFormat(lang, { maximumFractionDigits: 2 })
  const num = (n: number) => numberFormat.format(n)
  const lookup = (key: string, params: Params) => {
    const one = `${key}_one`
    const chosen = params.n === 1 && one in dict ? one : key
    return chosen in dict ? format(dict[chosen as Key], params, num) : null
  }
  return {
    lang,
    setLang,
    num,
    t: (key, params = {}) => lookup(key, params) ?? key,
    tm: (notice) =>
      typeof notice === 'string' ? notice : (lookup(`notice.${notice.code}`, notice.params) ?? notice.text),
  }
}

export const I18nContext = createContext<I18n | null>(null)

export function useI18n(): I18n {
  const i18n = useContext(I18nContext)
  if (!i18n) throw new Error('useI18n needs an I18nProvider')
  return i18n
}
