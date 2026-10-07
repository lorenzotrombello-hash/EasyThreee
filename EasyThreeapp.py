import csv
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

provini_nc = []
provini_ok = []
registro = []

# --- palette ---
SFONDO = "#f6f3ee"
CARTA = "#ffffff"
BORDO = "#e6dfd3"
TESTO = "#2e2a25"
TESTO_LEGGERO = "#857b6f"
TEAL = "#235e5a"
ARANCIO = "#e07b4a"
ARANCIO_SCURO = "#c96a3b"
VERDE = "#2f8352"
VERDE_CHIARO = "#e5f3ea"
CORALLO = "#cc4b45"
CORALLO_CHIARO = "#fbebea"
FONT = "Segoe UI"


def fmt(n):
    return f"{n:g}"


def leggi_numero(campo, nome):
    """Accetta sia il punto sia la virgola e solo numeri finiti."""
    testo = campo.get().strip().replace(",", ".")
    try:
        numero = float(testo)
    except ValueError:
        raise ValueError(f"{nome}: inserisci un numero valido")

    if not math.isfinite(numero):
        raise ValueError(f"{nome}: inserisci un numero valido")

    return numero


def calcola_requisiti(requisito_singolo, requisito_media, spessore):
    """Scala i requisiti e arrotonda entrambi per eccesso all'intero."""
    fattore = spessore / 10
    singolo = math.ceil(requisito_singolo * fattore)
    media = math.ceil(requisito_media * fattore)
    return fattore, singolo, media


# ---------------------------------------------------------------- logica dell'app
def mostra_esito(
    titolo, dettaglio, colore, sfondo,
    media_testo="", requisiti_testo=""
):
    riquadro_esito.config(bg=sfondo)
    media_label.config(text=media_testo, bg=sfondo)
    esito_titolo.config(text=titolo, fg=colore, bg=sfondo)
    esito_dettaglio.config(text=dettaglio, bg=sfondo)
    esito_requisiti.config(text=requisiti_testo, bg=sfondo)


def aggiorna_tabella():
    for riga in tabella.get_children():
        tabella.delete(riga)

    scelta = filtro.get()
    mostrate = [
        r for r in registro
        if scelta == "tutte"
        or (scelta == "ok" and r["ok"])
        or (scelta == "nc" and not r["ok"])
    ]

    # Mantiene l'ordine di inserimento: nuove terne in fondo.
    for r in mostrate:
        v1, v2, v3 = r["valori"]
        tabella.insert(
            "", "end",
            values=(
                r["codice"],
                fmt(r["spessore"]),
                fmt(v1),
                fmt(v2),
                fmt(v3),
                fmt(r["media"]),
                "Conforme" if r["ok"] else "Non conforme",
                r["motivo"]
            ),
            tags=("ok" if r["ok"] else "nc",)
        )

    kpi_tot.config(text=str(len(registro)))
    kpi_ok.config(text=str(len(provini_ok)))
    kpi_nc.config(text=str(len(provini_nc)))

    if mostrate:
        vuoto.place_forget()
    else:
        if registro:
            vuoto.config(text="Nessuna terna in questa categoria")
        else:
            vuoto.config(
                text="Nessuna terna ancora\n"
                     "Inserisci la prima a sinistra e premi Verifica"
            )
        vuoto.place(relx=0.5, rely=0.5, anchor="center")


def imposta_filtro(valore):
    filtro.set(valore)
    for chiave, b in bottoni_filtro.items():
        if chiave == valore:
            b.config(bg=TEAL, fg="white")
        else:
            b.config(bg=CARTA, fg=TESTO)
    aggiorna_tabella()


def aggiorna_requisiti(evento=None):
    """Aggiorna l'anteprima quando cambiano spessore o requisiti."""
    try:
        rs = leggi_numero(e_req_singolo, "Minimo singolo")
        rm = leggi_numero(e_req_media, "Minimo media")
        sp = leggi_numero(c_spessore, "Spessore")
    except ValueError:
        req_var.set("Requisiti applicati:  —")
        return

    if sp <= 0 or sp > 10:
        req_var.set("Spessore: maggiore di 0 e massimo 10 mm")
        return

    if rs < 0 or rm < 0:
        req_var.set("I requisiti non possono essere negativi")
        return

    fattore, req_singolo, req_media = calcola_requisiti(rs, rm, sp)
    req_var.set(
        f"Requisiti applicati ({fmt(round(fattore * 100, 1))}%):  "
        f"singolo {fmt(req_singolo)}  ·  media {fmt(req_media)}"
    )


def prova():
    try:
        requisito_singolo = leggi_numero(
            e_req_singolo, "Minimo singolo valore"
        )
        requisito_media = leggi_numero(
            e_req_media, "Minimo della media"
        )
        spessore = leggi_numero(c_spessore, "Spessore")
        J_1 = leggi_numero(e_j1, "Valore 1")
        J_2 = leggi_numero(e_j2, "Valore 2")
        J_3 = leggi_numero(e_j3, "Valore 3")
    except ValueError as errore:
        messagebox.showwarning("Dati non validi", str(errore))
        return

    codice = e_codice.get().strip()
    if codice == "":
        messagebox.showwarning(
            "Manca qualcosa", "Inserisci il codice della terna"
        )
        return

    if spessore <= 0 or spessore > 10:
        messagebox.showwarning(
            "Spessore non valido",
            "Lo spessore deve essere maggiore di 0 e al massimo 10 mm"
        )
        return

    if min(requisito_singolo, requisito_media, J_1, J_2, J_3) < 0:
        messagebox.showwarning(
            "Dati non validi",
            "Le energie e i requisiti non possono essere negativi"
        )
        return

    # Entrambi i requisiti sono arrotondati per eccesso.
    fattore, req_singolo, req_media = calcola_requisiti(
        requisito_singolo, requisito_media, spessore
    )

    requisiti_testo = (
        f"Spessore {fmt(spessore)} mm: "
        f"{fmt(round(fattore * 100, 1))}% dei requisiti\n"
        f"Minimo singolo {fmt(req_singolo)} J  ·  "
        f"Minimo media {fmt(req_media)} J"
    )

    # Media effettiva per la verifica.
    media = (J_1 + J_2 + J_3) / 3

    # Media intera per visualizzazione ed esportazione:
    # sotto 0,5 per difetto; da 0,5 in su per eccesso.
    media_visualizzata = math.floor(media + 0.5)
    media_testo = f"Media: {media_visualizzata} J"

    if min(J_1, J_2, J_3) < req_singolo:
        mostra_esito(
            "Non conforme",
            "Uno o più valori singoli sono inferiori al minimo richiesto",
            CORALLO, CORALLO_CHIARO,
            media_testo, requisiti_testo
        )
        provini_nc.append(codice)
        conforme, motivo = False, "valore singolo provino sotto il minimo"

    elif media < req_media:
        mostra_esito(
            "Non conforme",
            "I singoli valori rispettano il minimo ma la media "
            "non arrotondata è inferiore al minimo richiesto",
            CORALLO, CORALLO_CHIARO,
            media_testo, requisiti_testo
        )
        provini_nc.append(codice)
        conforme, motivo = False, "Media dei tre provini sotto il minimo"

    else:
        mostra_esito(
            "Terna conforme",
            "Tutti i valori e la media rispettano i requisiti",
            VERDE, VERDE_CHIARO,
            media_testo, requisiti_testo
        )
        provini_ok.append(codice)
        conforme, motivo = True, "—"

    registro.append({
        "codice": codice,
        "spessore": spessore,
        "valori": (J_1, J_2, J_3),
        "media": media_visualizzata,
        "media_effettiva": media,
        "ok": conforme,
        "motivo": motivo,
        "req_singolo": req_singolo,
        "req_media": req_media
    })

    aggiorna_tabella()

    # Mostra l'ultima riga aggiunta se è visibile nel filtro corrente.
    righe = tabella.get_children()
    if righe and (
        filtro.get() == "tutte"
        or (filtro.get() == "ok" and conforme)
        or (filtro.get() == "nc" and not conforme)
    ):
        tabella.see(righe[-1])

    for campo in (e_codice, e_j1, e_j2, e_j3):
        campo.delete(0, tk.END)
    e_codice.focus()


def azzera():
    if not registro:
        return

    if messagebox.askyesno(
        "Ricominciare?", "Vuoi cancellare tutte le terne inserite?"
    ):
        registro.clear()
        provini_ok.clear()
        provini_nc.clear()
        mostra_esito(
            "Pronto", "Inserisci i valori e premi Verifica",
            TESTO_LEGGERO, CARTA
        )
        aggiorna_tabella()


def esporta():
    if not registro:
        messagebox.showinfo(
            "Export Excel", "Non ci sono ancora terne da esportare"
        )
        return

    percorso = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV per Excel", "*.csv")],
        initialfile="terne_easythree.csv",
        title="Export Excel"
    )
    if not percorso:
        return

    try:
        with open(percorso, "w", newline="", encoding="utf-8-sig") as f:
            scrivi = csv.writer(f, delimiter=";")
            scrivi.writerow([
                "Codice",
                "Spessore (mm)",
                "Valore 1 (J)",
                "Valore 2 (J)",
                "Valore 3 (J)",
                "Media arrotondata (J)",
                "Esito",
                "Motivo",
                "Minimo singolo applicato (J)",
                "Minimo media applicato (J)"
            ])

            for r in registro:
                v1, v2, v3 = r["valori"]
                numeri = [
                    fmt(x).replace(".", ",")
                    for x in (r["spessore"], v1, v2, v3, r["media"])
                ]
                applicati = [
                    fmt(x).replace(".", ",")
                    for x in (r["req_singolo"], r["req_media"])
                ]
                scrivi.writerow([
                    r["codice"],
                    *numeri,
                    "Conforme" if r["ok"] else "Non conforme",
                    r["motivo"],
                    *applicati
                ])

        messagebox.showinfo(
            "Export Excel",
            "File CSV salvato. Lo puoi aprire con Excel."
        )
    except OSError as errore:
        messagebox.showerror(
            "Export Excel",
            f"Non sono riuscito a salvare il file:\n{errore}"
        )


# ---------------------------------------------------------------- elementi grafici
def carta(parent):
    return tk.Frame(
        parent, bg=CARTA,
        highlightthickness=1, highlightbackground=BORDO
    )


def titolo_sezione(parent, testo):
    return tk.Label(
        parent, text=testo, bg=CARTA, fg=TEAL,
        font=(FONT, 12, "bold")
    )


def etichetta_piccola(parent, testo):
    return tk.Label(
        parent, text=testo, bg=CARTA, fg=TESTO_LEGGERO,
        font=(FONT, 9)
    )


def casella(parent):
    return tk.Entry(
        parent, font=(FONT, 12), relief="flat",
        bg="#faf8f4", fg=TESTO, insertbackground=TESTO,
        highlightthickness=1,
        highlightbackground=BORDO,
        highlightcolor=ARANCIO
    )


def bottone(parent, testo, comando, stile="principale"):
    if stile == "principale":
        b = tk.Button(
            parent, text=testo, command=comando,
            font=(FONT, 12, "bold"),
            bg=ARANCIO, fg="white",
            activebackground=ARANCIO_SCURO,
            activeforeground="white",
            relief="flat", cursor="hand2", pady=11, bd=0
        )
        b.bind("<Enter>", lambda ev: b.config(bg=ARANCIO_SCURO))
        b.bind("<Leave>", lambda ev: b.config(bg=ARANCIO))

    elif stile == "secondario":
        b = tk.Button(
            parent, text=testo, command=comando,
            font=(FONT, 10, "bold"),
            bg=CARTA, fg=TEAL,
            activebackground="#eef4f3",
            activeforeground=TEAL,
            relief="flat", cursor="hand2",
            padx=14, pady=6,
            highlightthickness=1,
            highlightbackground=TEAL, bd=0
        )

    else:
        b = tk.Button(
            parent, text=testo, command=comando,
            font=(FONT, 10),
            bg=SFONDO, fg=TESTO_LEGGERO,
            activebackground=SFONDO,
            activeforeground=TESTO,
            relief="flat", cursor="hand2", bd=0, padx=8
        )

    return b


# ---------------------------------------------------------------- finestra
root = tk.Tk()
root.title("EasyThree")
root.configure(bg=SFONDO)

larghezza, altezza = 1120, 680
x = max(0, (root.winfo_screenwidth() - larghezza) // 2)
y = max(0, (root.winfo_screenheight() - altezza) // 2 - 20)
root.geometry(f"{larghezza}x{altezza}+{x}+{y}")
root.minsize(1000, 620)

filtro = tk.StringVar(value="tutte")
req_var = tk.StringVar()

stile = ttk.Style()
stile.theme_use("clam")
stile.configure(
    "Treeview",
    background=CARTA, fieldbackground=CARTA,
    foreground=TESTO, rowheight=32,
    font=(FONT, 11), borderwidth=0
)
stile.configure(
    "Treeview.Heading",
    background="#eef2f1", foreground=TEAL,
    font=(FONT, 10, "bold"),
    relief="flat", padding=(8, 9)
)
stile.map(
    "Treeview.Heading",
    background=[("active", "#e2ebe9")]
)
stile.map(
    "Treeview",
    background=[("selected", "#dcebe8")],
    foreground=[("selected", TESTO)]
)
stile.configure(
    "TCombobox",
    padding=5, fieldbackground="#faf8f4",
    background=CARTA, arrowcolor=TEAL,
    bordercolor=BORDO, lightcolor=BORDO, darkcolor=BORDO
)
root.option_add("*TCombobox*Listbox.font", (FONT, 11))

# ---- intestazione
ora = datetime.now().hour
saluto = (
    "Buongiorno" if ora < 12
    else "Buon pomeriggio" if ora < 18
    else "Buonasera"
)

header = tk.Frame(root, bg=TEAL)
header.pack(fill="x")

tk.Label(
    header, text="EasyThree",
    bg=TEAL, fg="white",
    font=(FONT, 20, "bold")
).pack(side="left", padx=(24, 12), pady=14)

tk.Label(
    header, text="Verifica delle terne di resilienza",
    bg=TEAL, fg="#b9d6d2", font=(FONT, 11)
).pack(side="left", pady=(6, 0))

tk.Label(
    header, text=f"{saluto}!",
    bg=TEAL, fg="white", font=(FONT, 12)
).pack(side="right", padx=24)

corpo = tk.Frame(root, bg=SFONDO)
corpo.pack(fill="both", expand=True, padx=20, pady=16)
corpo.columnconfigure(1, weight=1)
corpo.rowconfigure(0, weight=1)

sinistra = tk.Frame(corpo, bg=SFONDO)
sinistra.grid(row=0, column=0, sticky="ns", padx=(0, 16))
sinistra.columnconfigure(0, weight=1, minsize=340)

destra = tk.Frame(corpo, bg=SFONDO)
destra.grid(row=0, column=1, sticky="nsew")
destra.columnconfigure(0, weight=1)
destra.rowconfigure(2, weight=1)

# ---- requisiti
card_req = carta(sinistra)
card_req.grid(row=0, column=0, sticky="ew")
card_req.columnconfigure(0, weight=1)
card_req.columnconfigure(1, weight=1)

titolo_sezione(card_req, "Requisiti per provino 10 × 10 mm").grid(
    row=0, column=0, columnspan=2,
    sticky="w", padx=16, pady=(14, 8)
)

etichetta_piccola(card_req, "Minimo singolo valore (J)").grid(
    row=1, column=0, sticky="w", padx=(16, 6)
)
etichetta_piccola(card_req, "Minimo della media (J)").grid(
    row=1, column=1, sticky="w", padx=(6, 16)
)

e_req_singolo = casella(card_req)
e_req_singolo.grid(
    row=2, column=0, sticky="ew",
    padx=(16, 6), pady=(3, 16), ipady=6
)

e_req_media = casella(card_req)
e_req_media.grid(
    row=2, column=1, sticky="ew",
    padx=(6, 16), pady=(3, 16), ipady=6
)

# ---- nuova terna
card_terna = carta(sinistra)
card_terna.grid(row=1, column=0, sticky="ew", pady=(12, 0))

for c in range(3):
    card_terna.columnconfigure(c, weight=1)

titolo_sezione(card_terna, "Nuova terna").grid(
    row=0, column=0, columnspan=3,
    sticky="w", padx=16, pady=(14, 8)
)

etichetta_piccola(card_terna, "Codice").grid(
    row=1, column=0, columnspan=2, sticky="w", padx=16
)
etichetta_piccola(card_terna, "Spessore (mm)").grid(
    row=1, column=2, sticky="w", padx=(4, 16)
)

e_codice = casella(card_terna)
e_codice.grid(
    row=2, column=0, columnspan=2,
    sticky="ew", padx=(16, 4), pady=(3, 12), ipady=6
)

c_spessore = ttk.Combobox(
    card_terna,
    values=("10", "7.5", "5", "2.5"),
    font=(FONT, 12), width=6
)
c_spessore.set("10")
c_spessore.grid(
    row=2, column=2, sticky="ew",
    padx=(4, 16), pady=(3, 12)
)

tk.Label(
    card_terna, textvariable=req_var,
    bg="#e8f1ef", fg=TEAL,
    font=(FONT, 10, "bold"),
    anchor="w", padx=12, pady=7
).grid(
    row=3, column=0, columnspan=3,
    sticky="ew", padx=16, pady=(0, 12)
)

margini = [(16, 4), (4, 4), (4, 16)]
campi_valori = []

for i, nome in enumerate(["Valore 1 (J)", "Valore 2 (J)", "Valore 3 (J)"]):
    etichetta_piccola(card_terna, nome).grid(
        row=4, column=i, sticky="w", padx=margini[i]
    )
    e = casella(card_terna)
    e.grid(
        row=5, column=i, sticky="ew",
        padx=margini[i], pady=(3, 16), ipady=6
    )
    campi_valori.append(e)

e_j1, e_j2, e_j3 = campi_valori

for campo in (e_req_singolo, e_req_media, c_spessore):
    campo.bind("<KeyRelease>", aggiorna_requisiti)

c_spessore.bind("<<ComboboxSelected>>", aggiorna_requisiti)

# Invio passa al campo successivo; dall'ultimo avvia la verifica.
sequenza = [e_codice, e_j1, e_j2, e_j3]

for i, campo in enumerate(sequenza):
    if i < len(sequenza) - 1:
        campo.bind(
            "<Return>",
            lambda ev, prossimo=sequenza[i + 1]: prossimo.focus()
        )
    else:
        campo.bind("<Return>", lambda ev: prova())

bottone(sinistra, "Verifica la terna", prova).grid(
    row=2, column=0, sticky="ew", pady=(14, 0)
)

# ---- esito
riquadro_esito = tk.Frame(
    sinistra, bg=CARTA,
    highlightthickness=1, highlightbackground=BORDO
)
riquadro_esito.grid(row=3, column=0, sticky="ew", pady=(14, 0))

media_label = tk.Label(
    riquadro_esito, text="", bg=CARTA, fg=TEAL,
    font=(FONT, 10, "bold")
)
media_label.pack(pady=(12, 0))

esito_titolo = tk.Label(
    riquadro_esito, text="Pronto",
    bg=CARTA, fg=TESTO_LEGGERO,
    font=(FONT, 15, "bold")
)
esito_titolo.pack(pady=(2, 0))

esito_dettaglio = tk.Label(
    riquadro_esito, text="Inserisci i valori e premi Verifica",
    bg=CARTA, fg=TESTO, font=(FONT, 10),
    wraplength=300, justify="center"
)
esito_dettaglio.pack(pady=(2, 0), padx=14)

esito_requisiti = tk.Label(
    riquadro_esito, text="",
    bg=CARTA, fg=TESTO_LEGGERO,
    font=(FONT, 9), justify="center"
)
esito_requisiti.pack(pady=(6, 12), padx=14)

# ---- riepilogo
riepilogo = tk.Frame(destra, bg=SFONDO)
riepilogo.grid(row=0, column=0, sticky="ew")

for c in range(3):
    riepilogo.columnconfigure(c, weight=1)


def scheda_numero(colonna, didascalia, colore, margine):
    s = carta(riepilogo)
    s.grid(row=0, column=colonna, sticky="ew", padx=margine)

    numero = tk.Label(
        s, text="0", bg=CARTA, fg=colore,
        font=(FONT, 26, "bold")
    )
    numero.pack(pady=(10, 0))

    tk.Label(
        s, text=didascalia,
        bg=CARTA, fg=TESTO_LEGGERO,
        font=(FONT, 10)
    ).pack(pady=(0, 10))

    return numero


kpi_tot = scheda_numero(0, "Terne provate", TEAL, (0, 6))
kpi_ok = scheda_numero(1, "Conformi", VERDE, (6, 6))
kpi_nc = scheda_numero(2, "Non conformi", CORALLO, (6, 0))

# ---- barra degli strumenti
barra = tk.Frame(destra, bg=SFONDO)
barra.grid(row=1, column=0, sticky="ew", pady=(14, 8))

segmento = tk.Frame(barra, bg=BORDO, padx=1, pady=1)
segmento.pack(side="left")

bottoni_filtro = {}

for chiave, testo in (
    ("tutte", "Tutte"),
    ("ok", "Conformi"),
    ("nc", "Non conformi")
):
    b = tk.Button(
        segmento, text=testo, font=(FONT, 10, "bold"),
        relief="flat", bd=0, padx=16, pady=6,
        cursor="hand2", bg=CARTA, fg=TESTO,
        activebackground=CARTA,
        command=lambda k=chiave: imposta_filtro(k)
    )
    b.pack(side="left")
    bottoni_filtro[chiave] = b

bottone(
    barra, "Ricomincia da capo", azzera, "testo"
).pack(side="right")

bottone(
    barra, "Export Excel", esporta, "secondario"
).pack(side="right", padx=(0, 8))

# ---- tabella delle terne
card_tabella = carta(destra)
card_tabella.grid(row=2, column=0, sticky="nsew")
card_tabella.columnconfigure(0, weight=1)
card_tabella.rowconfigure(0, weight=1)

colonne = (
    "codice", "spessore", "v1", "v2", "v3",
    "media", "esito", "motivo"
)

tabella = ttk.Treeview(
    card_tabella, columns=colonne,
    show="headings", selectmode="browse"
)

intestazioni = {
    "codice": ("Codice", 90, "w"),
    "spessore": ("Sp. mm", 70, "center"),
    "v1": ("Valore 1", 66, "center"),
    "v2": ("Valore 2", 66, "center"),
    "v3": ("Valore 3", 66, "center"),
    "media": ("Media", 66, "center"),
    "esito": ("Esito", 104, "center"),
    "motivo": ("Motivo", 170, "w")
}

for nome, (testo, largo, ancora) in intestazioni.items():
    tabella.heading(nome, text=testo, anchor=ancora)
    tabella.column(
        nome, width=largo, anchor=ancora,
        stretch=(nome == "motivo")
    )

tabella.tag_configure(
    "ok", foreground=VERDE, background="#f4faf6"
)
tabella.tag_configure(
    "nc", foreground=CORALLO, background="#fdf4f3"
)
tabella.grid(
    row=0, column=0, sticky="nsew",
    padx=(1, 0), pady=1
)

barra_scorrimento = ttk.Scrollbar(
    card_tabella, orient="vertical", command=tabella.yview
)
barra_scorrimento.grid(row=0, column=1, sticky="ns", pady=1)
tabella.configure(yscrollcommand=barra_scorrimento.set)

vuoto = tk.Label(
    card_tabella, text="",
    bg=CARTA, fg=TESTO_LEGGERO,
    font=(FONT, 11), justify="center"
)

# ---- valori iniziali
e_req_singolo.insert(0, "27")
e_req_media.insert(0, "30")

imposta_filtro("tutte")
aggiorna_requisiti()
e_codice.focus()

root.mainloop()