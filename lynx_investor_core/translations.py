"""Lightweight in-memory translation registry for the Lince Investor Suite.

Distinct from the older :mod:`lynx_investor_core.i18n` (which is a
``gettext`` wrapper meant for full PO/MO catalogues) — this module is a
much smaller dict-based store designed for the fixed set of widely
re-used UI strings (button labels, section titles, common verbs,
common nouns). Every Suite app imports from here, so adding a new
language requires editing exactly one file.

Supported language codes (case-insensitive on input, lowercased
internally):

* ``us`` — English (default)
* ``es`` — Spanish
* ``it`` — Italian
* ``de`` — German
* ``fr`` — French
* ``fa`` — Farsi / Persian (right-to-left rendering is up to the
  caller; this module returns the strings as-is)

The chosen language persists to ``$XDG_CONFIG_HOME/lynx/language.json``
(or ``~/.config/lynx/language.json``) so every Suite app starts up in
the user's preferred language. The ``LYNX_LANG`` env-var overrides
that file for ad-hoc shells (e.g. ``LYNX_LANG=es lynx-fund -i``).

The ``--language=XX`` CLI flag is wired into every Suite parser via
:func:`add_language_argument` and applied via :func:`apply_args`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Optional

__all__ = [
    "SUPPORTED_LANGUAGES",
    "LANG_LABELS",
    "DEFAULT_LANGUAGE",
    "set_language",
    "current_language",
    "cycle_language",
    "t",
    "tr",
    "add_language_argument",
    "apply_args",
    "language_storage_path",
]


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

DEFAULT_LANGUAGE = "us"

#: Ordered tuple of supported language codes — used by the round-robin
#: GUI / TUI corner toggle.
SUPPORTED_LANGUAGES: tuple[str, ...] = ("us", "es", "it", "de", "fr", "fa")

LANG_LABELS: dict[str, str] = {
    "us": "EN",  # short label for buttons (US flag region uses "EN" badge)
    "es": "ES",
    "it": "IT",
    "de": "DE",
    "fr": "FR",
    "fa": "FA",
}

LANG_FULL_NAMES: dict[str, str] = {
    "us": "English (US)",
    "es": "Español",
    "it": "Italiano",
    "de": "Deutsch",
    "fr": "Français",
    "fa": "فارسی (Persian)",
}

# Translation table — every key is a stable identifier the code uses;
# every value is the display string in that language. Missing keys
# silently fall through to the US text.
TRANSLATIONS: dict[str, dict[str, str]] = {
    "us": {
        "metric": "Metric",
        "assessment": "Assessment",
        "interpretation": "Interpretation",
        "note": "Note",
        "category": "Category",
        "field": "Field",
        "label": "Label",
        "status": "Status",
        "check": "Check",
        "rule_of_thumb": "Rule of thumb",
        "fund_profile": "Fund Profile",
        "etf_profile": "ETF Profile",
        "company_profile": "Company Profile",
        "tier": "Tier",
        "domicile": "Domicile",
        "asset_class": "Asset Class",
        "family": "Family",
        "inception": "Inception",
        "benchmark": "Benchmark",
        "distribution": "Distribution",
        "size_tier": "Size Tier",
        "aum": "AUM",
        "mode": "Mode",
        "ready_status": "Ready.",
        "analyzing": "Analysing…",
        "comparing": "Comparing…",
        "exporting": "Exporting…",
        "verdict": "Verdict",
        "strengths": "Strengths",
        "risks": "Risks",
        "suitable_for": "Suitable for",
        "category_scores": "Category Scores",
        "passive_verdict": "Passive Investor Verdict",
        "section_result": "SECTION RESULT",
        "fund_ticker": "Fund Ticker",
        "etf_ticker": "ETF Ticker",
        "ticker_or_isin": "Ticker or ISIN",
        "mode_testing": "TESTING",
        "mode_production": "PRODUCTION",
        # Common nouns
        "ticker": "Ticker",
        "name": "Name",
        "price": "Price",
        "ratio": "Ratio",
        "yield": "Yield",
        "ratio_pct": "% Ratio",
        "value": "Value",
        "score": "Score",
        "summary": "Summary",
        "details": "Details",
        "description": "Description",
        # Verbs / actions
        "analyse": "Analyse",
        "compare": "Compare",
        "search": "Search",
        "save": "Save",
        "save_as": "Save As",
        "load": "Load",
        "open": "Open",
        "close": "Close",
        "quit": "Quit",
        "cancel": "Cancel",
        "ok": "OK",
        "refresh": "Refresh",
        "export": "Export",
        "preview": "Preview",
        "set_default": "Set as Default",
        "set_language": "Language",
        "back": "Back",
        # Labels
        "ready": "Ready.",
        "done": "Done.",
        "error": "Error.",
        "loading": "Loading…",
        "working": "Working…",
        "no_data": "N/A",
        "warning": "Warning",
        "success": "Success",
        "info": "Info",
        # Sections
        "costs": "Costs",
        "income": "Income",
        "liquidity": "Size & Liquidity",
        "performance": "Performance",
        "risk": "Risk",
        "allocation": "Allocation",
        "diversification": "Diversification",
        "manager": "Management",
        "tax": "Tax",
        "tracking": "Tracking",
        "share_classes": "Share Classes",
        "structure": "Structure & Regulation",
        "passive_checklist": "Passive Investor Checklist",
        "tips_for_passive_investors": "Tips for Passive Investors",
        # Tabs / hero
        "fund_ticker_or_isin": "Fund Ticker or ISIN:",
        "etf_ticker_or_isin": "ETF Ticker or ISIN:",
        "fund_a": "Fund A:",
        "fund_b": "Fund B:",
        "etf_a": "ETF A:",
        "etf_b": "ETF B:",
        # Verdict words
        "strong_buy": "Strong Buy",
        "buy": "Buy",
        "hold": "Hold",
        "caution": "Caution",
        "avoid": "Avoid",
        # Misc
        "language": "Language",
        "language_us": "English (US)",
        "language_es": "Español",
        "language_it": "Italiano",
        "language_de": "Deutsch",
        "language_fr": "Français",
        "language_fa": "فارسی",
        "about": "About",
        "version": "Version",
        "license": "License",
        "developed_by": "Developed by",
        "contact": "Contact",
    },
    "es": {
        "metric": "Métrica",
        "assessment": "Valoración",
        "interpretation": "Interpretación",
        "note": "Nota",
        "category": "Categoría",
        "field": "Campo",
        "label": "Etiqueta",
        "status": "Estado",
        "check": "Comprobación",
        "rule_of_thumb": "Regla práctica",
        "fund_profile": "Perfil del fondo",
        "etf_profile": "Perfil del ETF",
        "company_profile": "Perfil de la empresa",
        "tier": "Categoría",
        "domicile": "Domicilio",
        "asset_class": "Clase de activo",
        "family": "Familia",
        "inception": "Inicio",
        "benchmark": "Índice de referencia",
        "distribution": "Distribución",
        "size_tier": "Tamaño",
        "aum": "Patrimonio (AUM)",
        "mode": "Modo",
        "ready_status": "Listo.",
        "analyzing": "Analizando…",
        "comparing": "Comparando…",
        "exporting": "Exportando…",
        "verdict": "Veredicto",
        "strengths": "Puntos fuertes",
        "risks": "Riesgos",
        "suitable_for": "Adecuado para",
        "category_scores": "Puntuaciones por categoría",
        "passive_verdict": "Veredicto del inversor pasivo",
        "section_result": "RESULTADO DE LA SECCIÓN",
        "fund_ticker": "Ticker del fondo",
        "etf_ticker": "Ticker del ETF",
        "ticker_or_isin": "Ticker o ISIN",
        "mode_testing": "PRUEBAS",
        "mode_production": "PRODUCCIÓN",
        "ticker": "Ticker",
        "name": "Nombre",
        "price": "Precio",
        "ratio": "Ratio",
        "yield": "Rendimiento",
        "ratio_pct": "% Ratio",
        "value": "Valor",
        "score": "Puntuación",
        "summary": "Resumen",
        "details": "Detalles",
        "description": "Descripción",
        "analyse": "Analizar",
        "compare": "Comparar",
        "search": "Buscar",
        "save": "Guardar",
        "save_as": "Guardar como",
        "load": "Cargar",
        "open": "Abrir",
        "close": "Cerrar",
        "quit": "Salir",
        "cancel": "Cancelar",
        "ok": "Aceptar",
        "refresh": "Actualizar",
        "export": "Exportar",
        "preview": "Previsualizar",
        "set_default": "Establecer por defecto",
        "set_language": "Idioma",
        "back": "Atrás",
        "ready": "Listo.",
        "done": "Hecho.",
        "error": "Error.",
        "loading": "Cargando…",
        "working": "Trabajando…",
        "no_data": "N/D",
        "warning": "Aviso",
        "success": "Éxito",
        "info": "Información",
        "costs": "Costes",
        "income": "Ingresos",
        "liquidity": "Tamaño y liquidez",
        "performance": "Rentabilidad",
        "risk": "Riesgo",
        "allocation": "Asignación",
        "diversification": "Diversificación",
        "manager": "Gestión",
        "tax": "Fiscalidad",
        "tracking": "Seguimiento",
        "share_classes": "Clases de participaciones",
        "structure": "Estructura y regulación",
        "passive_checklist": "Lista del inversor pasivo",
        "tips_for_passive_investors": "Consejos para inversores pasivos",
        "fund_ticker_or_isin": "Ticker o ISIN del fondo:",
        "etf_ticker_or_isin": "Ticker o ISIN del ETF:",
        "fund_a": "Fondo A:",
        "fund_b": "Fondo B:",
        "etf_a": "ETF A:",
        "etf_b": "ETF B:",
        "strong_buy": "Compra fuerte",
        "buy": "Compra",
        "hold": "Mantener",
        "caution": "Precaución",
        "avoid": "Evitar",
        "language": "Idioma",
        "about": "Acerca de",
        "version": "Versión",
        "license": "Licencia",
        "developed_by": "Desarrollado por",
        "contact": "Contacto",
    },
    "it": {
        "metric": "Metrica",
        "assessment": "Valutazione",
        "interpretation": "Interpretazione",
        "note": "Nota",
        "category": "Categoria",
        "field": "Campo",
        "label": "Etichetta",
        "status": "Stato",
        "check": "Verifica",
        "rule_of_thumb": "Regola pratica",
        "fund_profile": "Profilo del fondo",
        "etf_profile": "Profilo dell'ETF",
        "company_profile": "Profilo aziendale",
        "tier": "Categoria",
        "domicile": "Domicilio",
        "asset_class": "Classe di attività",
        "family": "Famiglia",
        "inception": "Inizio",
        "benchmark": "Benchmark",
        "distribution": "Distribuzione",
        "size_tier": "Dimensione",
        "aum": "Patrimonio (AUM)",
        "mode": "Modalità",
        "ready_status": "Pronto.",
        "analyzing": "Analisi in corso…",
        "comparing": "Confronto in corso…",
        "exporting": "Esportazione…",
        "verdict": "Verdetto",
        "strengths": "Punti di forza",
        "risks": "Rischi",
        "suitable_for": "Adatto per",
        "category_scores": "Punteggi per categoria",
        "passive_verdict": "Verdetto investitore passivo",
        "section_result": "RISULTATO SEZIONE",
        "fund_ticker": "Ticker del fondo",
        "etf_ticker": "Ticker dell'ETF",
        "ticker_or_isin": "Ticker o ISIN",
        "mode_testing": "TEST",
        "mode_production": "PRODUZIONE",
        "ticker": "Ticker",
        "name": "Nome",
        "price": "Prezzo",
        "ratio": "Rapporto",
        "yield": "Rendimento",
        "value": "Valore",
        "score": "Punteggio",
        "summary": "Riepilogo",
        "details": "Dettagli",
        "description": "Descrizione",
        "analyse": "Analizza",
        "compare": "Confronta",
        "search": "Cerca",
        "save": "Salva",
        "save_as": "Salva come",
        "load": "Carica",
        "open": "Apri",
        "close": "Chiudi",
        "quit": "Esci",
        "cancel": "Annulla",
        "ok": "OK",
        "refresh": "Aggiorna",
        "export": "Esporta",
        "preview": "Anteprima",
        "set_default": "Imposta come predefinito",
        "set_language": "Lingua",
        "back": "Indietro",
        "ready": "Pronto.",
        "done": "Fatto.",
        "error": "Errore.",
        "loading": "Caricamento…",
        "working": "In esecuzione…",
        "no_data": "N/D",
        "warning": "Avviso",
        "success": "Successo",
        "info": "Info",
        "costs": "Costi",
        "income": "Reddito",
        "liquidity": "Dimensione e liquidità",
        "performance": "Performance",
        "risk": "Rischio",
        "allocation": "Allocazione",
        "diversification": "Diversificazione",
        "manager": "Gestione",
        "tax": "Fiscalità",
        "tracking": "Replica",
        "share_classes": "Classi di quote",
        "structure": "Struttura e regolamentazione",
        "passive_checklist": "Checklist investitore passivo",
        "tips_for_passive_investors": "Consigli per investitori passivi",
        "fund_ticker_or_isin": "Ticker o ISIN del fondo:",
        "etf_ticker_or_isin": "Ticker o ISIN dell'ETF:",
        "fund_a": "Fondo A:",
        "fund_b": "Fondo B:",
        "etf_a": "ETF A:",
        "etf_b": "ETF B:",
        "strong_buy": "Forte acquisto",
        "buy": "Acquista",
        "hold": "Mantieni",
        "caution": "Attenzione",
        "avoid": "Evitare",
        "language": "Lingua",
        "about": "Informazioni",
        "version": "Versione",
        "license": "Licenza",
        "developed_by": "Sviluppato da",
        "contact": "Contatto",
    },
    "de": {
        "metric": "Kennzahl",
        "assessment": "Bewertung",
        "interpretation": "Interpretation",
        "note": "Hinweis",
        "category": "Kategorie",
        "field": "Feld",
        "label": "Bezeichnung",
        "status": "Status",
        "check": "Prüfung",
        "rule_of_thumb": "Faustregel",
        "fund_profile": "Fonds-Profil",
        "etf_profile": "ETF-Profil",
        "company_profile": "Unternehmensprofil",
        "tier": "Kategorie",
        "domicile": "Domizil",
        "asset_class": "Anlageklasse",
        "family": "Familie",
        "inception": "Auflegung",
        "benchmark": "Benchmark",
        "distribution": "Ausschüttung",
        "size_tier": "Grösse",
        "aum": "Vermögen (AUM)",
        "mode": "Modus",
        "ready_status": "Bereit.",
        "analyzing": "Analyse läuft…",
        "comparing": "Vergleich läuft…",
        "exporting": "Export läuft…",
        "verdict": "Urteil",
        "strengths": "Stärken",
        "risks": "Risiken",
        "suitable_for": "Geeignet für",
        "category_scores": "Kategorie-Bewertungen",
        "passive_verdict": "Urteil passiver Anleger",
        "section_result": "ABSCHNITTSERGEBNIS",
        "fund_ticker": "Fonds-Ticker",
        "etf_ticker": "ETF-Ticker",
        "ticker_or_isin": "Ticker oder ISIN",
        "mode_testing": "TEST",
        "mode_production": "PRODUKTION",
        "ticker": "Ticker",
        "name": "Name",
        "price": "Preis",
        "ratio": "Verhältnis",
        "yield": "Rendite",
        "value": "Wert",
        "score": "Bewertung",
        "summary": "Zusammenfassung",
        "details": "Details",
        "description": "Beschreibung",
        "analyse": "Analysieren",
        "compare": "Vergleichen",
        "search": "Suchen",
        "save": "Speichern",
        "save_as": "Speichern unter",
        "load": "Laden",
        "open": "Öffnen",
        "close": "Schließen",
        "quit": "Beenden",
        "cancel": "Abbrechen",
        "ok": "OK",
        "refresh": "Aktualisieren",
        "export": "Exportieren",
        "preview": "Vorschau",
        "set_default": "Als Standard festlegen",
        "set_language": "Sprache",
        "back": "Zurück",
        "ready": "Bereit.",
        "done": "Fertig.",
        "error": "Fehler.",
        "loading": "Wird geladen…",
        "working": "In Bearbeitung…",
        "no_data": "k. A.",
        "warning": "Warnung",
        "success": "Erfolg",
        "info": "Info",
        "costs": "Kosten",
        "income": "Erträge",
        "liquidity": "Größe & Liquidität",
        "performance": "Performance",
        "risk": "Risiko",
        "allocation": "Allokation",
        "diversification": "Diversifikation",
        "manager": "Management",
        "tax": "Steuern",
        "tracking": "Tracking",
        "share_classes": "Anteilklassen",
        "structure": "Struktur & Regulierung",
        "passive_checklist": "Checkliste passive Anleger",
        "tips_for_passive_investors": "Tipps für passive Anleger",
        "fund_ticker_or_isin": "Fonds-Ticker oder ISIN:",
        "etf_ticker_or_isin": "ETF-Ticker oder ISIN:",
        "fund_a": "Fonds A:",
        "fund_b": "Fonds B:",
        "etf_a": "ETF A:",
        "etf_b": "ETF B:",
        "strong_buy": "Stark kaufen",
        "buy": "Kaufen",
        "hold": "Halten",
        "caution": "Vorsicht",
        "avoid": "Meiden",
        "language": "Sprache",
        "about": "Über",
        "version": "Version",
        "license": "Lizenz",
        "developed_by": "Entwickelt von",
        "contact": "Kontakt",
    },
    "fr": {
        "metric": "Métrique",
        "assessment": "Évaluation",
        "interpretation": "Interprétation",
        "note": "Note",
        "category": "Catégorie",
        "field": "Champ",
        "label": "Libellé",
        "status": "Statut",
        "check": "Vérification",
        "rule_of_thumb": "Règle empirique",
        "fund_profile": "Profil du fonds",
        "etf_profile": "Profil de l'ETF",
        "company_profile": "Profil de l'entreprise",
        "tier": "Catégorie",
        "domicile": "Domicile",
        "asset_class": "Classe d'actif",
        "family": "Famille",
        "inception": "Création",
        "benchmark": "Indice de référence",
        "distribution": "Distribution",
        "size_tier": "Taille",
        "aum": "Encours (AUM)",
        "mode": "Mode",
        "ready_status": "Prêt.",
        "analyzing": "Analyse en cours…",
        "comparing": "Comparaison en cours…",
        "exporting": "Exportation…",
        "verdict": "Verdict",
        "strengths": "Points forts",
        "risks": "Risques",
        "suitable_for": "Convient pour",
        "category_scores": "Scores par catégorie",
        "passive_verdict": "Verdict de l'investisseur passif",
        "section_result": "RÉSULTAT DE LA SECTION",
        "fund_ticker": "Ticker du fonds",
        "etf_ticker": "Ticker de l'ETF",
        "ticker_or_isin": "Ticker ou ISIN",
        "mode_testing": "TEST",
        "mode_production": "PRODUCTION",
        "ticker": "Ticker",
        "name": "Nom",
        "price": "Prix",
        "ratio": "Ratio",
        "yield": "Rendement",
        "value": "Valeur",
        "score": "Score",
        "summary": "Résumé",
        "details": "Détails",
        "description": "Description",
        "analyse": "Analyser",
        "compare": "Comparer",
        "search": "Rechercher",
        "save": "Enregistrer",
        "save_as": "Enregistrer sous",
        "load": "Charger",
        "open": "Ouvrir",
        "close": "Fermer",
        "quit": "Quitter",
        "cancel": "Annuler",
        "ok": "OK",
        "refresh": "Actualiser",
        "export": "Exporter",
        "preview": "Aperçu",
        "set_default": "Définir par défaut",
        "set_language": "Langue",
        "back": "Retour",
        "ready": "Prêt.",
        "done": "Terminé.",
        "error": "Erreur.",
        "loading": "Chargement…",
        "working": "En cours…",
        "no_data": "N/D",
        "warning": "Avertissement",
        "success": "Succès",
        "info": "Info",
        "costs": "Frais",
        "income": "Revenus",
        "liquidity": "Taille & liquidité",
        "performance": "Performance",
        "risk": "Risque",
        "allocation": "Allocation",
        "diversification": "Diversification",
        "manager": "Gestion",
        "tax": "Fiscalité",
        "tracking": "Réplication",
        "share_classes": "Classes de parts",
        "structure": "Structure & réglementation",
        "passive_checklist": "Checklist investisseur passif",
        "tips_for_passive_investors": "Conseils pour investisseurs passifs",
        "fund_ticker_or_isin": "Ticker ou ISIN du fonds :",
        "etf_ticker_or_isin": "Ticker ou ISIN de l'ETF :",
        "fund_a": "Fonds A :",
        "fund_b": "Fonds B :",
        "etf_a": "ETF A :",
        "etf_b": "ETF B :",
        "strong_buy": "Achat fort",
        "buy": "Acheter",
        "hold": "Conserver",
        "caution": "Prudence",
        "avoid": "Éviter",
        "language": "Langue",
        "about": "À propos",
        "version": "Version",
        "license": "Licence",
        "developed_by": "Développé par",
        "contact": "Contact",
    },
    "fa": {
        "metric": "معیار",
        "assessment": "ارزیابی",
        "interpretation": "تفسیر",
        "note": "یادداشت",
        "category": "دسته",
        "field": "فیلد",
        "label": "برچسب",
        "status": "وضعیت",
        "check": "بررسی",
        "rule_of_thumb": "قاعده عمومی",
        "fund_profile": "پروفایل صندوق",
        "etf_profile": "پروفایل ETF",
        "company_profile": "پروفایل شرکت",
        "tier": "رده",
        "domicile": "اقامت",
        "asset_class": "کلاس دارایی",
        "family": "خانواده",
        "inception": "آغاز",
        "benchmark": "شاخص مرجع",
        "distribution": "توزیع",
        "size_tier": "اندازه",
        "aum": "دارایی تحت مدیریت",
        "mode": "حالت",
        "ready_status": "آماده.",
        "analyzing": "در حال تحلیل…",
        "comparing": "در حال مقایسه…",
        "exporting": "در حال خروجی…",
        "verdict": "حکم",
        "strengths": "نقاط قوت",
        "risks": "ریسک‌ها",
        "suitable_for": "مناسب برای",
        "category_scores": "امتیاز هر دسته",
        "passive_verdict": "حکم سرمایه‌گذار غیرفعال",
        "section_result": "نتیجه بخش",
        "fund_ticker": "نماد صندوق",
        "etf_ticker": "نماد ETF",
        "ticker_or_isin": "نماد یا ISIN",
        "mode_testing": "آزمایشی",
        "mode_production": "تولید",
        "ticker": "نماد",
        "name": "نام",
        "price": "قیمت",
        "ratio": "نسبت",
        "yield": "بازده",
        "value": "ارزش",
        "score": "امتیاز",
        "summary": "خلاصه",
        "details": "جزئیات",
        "description": "توضیحات",
        "analyse": "تحلیل",
        "compare": "مقایسه",
        "search": "جستجو",
        "save": "ذخیره",
        "save_as": "ذخیره با نام",
        "load": "بارگذاری",
        "open": "باز کردن",
        "close": "بستن",
        "quit": "خروج",
        "cancel": "لغو",
        "ok": "تأیید",
        "refresh": "به‌روزرسانی",
        "export": "خروجی گرفتن",
        "preview": "پیش‌نمایش",
        "set_default": "تنظیم به‌عنوان پیش‌فرض",
        "set_language": "زبان",
        "back": "بازگشت",
        "ready": "آماده.",
        "done": "انجام شد.",
        "error": "خطا.",
        "loading": "در حال بارگذاری…",
        "working": "در حال اجرا…",
        "no_data": "نامشخص",
        "warning": "هشدار",
        "success": "موفق",
        "info": "اطلاعات",
        "costs": "هزینه‌ها",
        "income": "درآمد",
        "liquidity": "اندازه و نقدشوندگی",
        "performance": "عملکرد",
        "risk": "ریسک",
        "allocation": "تخصیص",
        "diversification": "تنوع",
        "manager": "مدیریت",
        "tax": "مالیات",
        "tracking": "ردیابی",
        "share_classes": "طبقه‌بندی سهام",
        "structure": "ساختار و مقررات",
        "passive_checklist": "چک‌لیست سرمایه‌گذار غیرفعال",
        "tips_for_passive_investors": "نکاتی برای سرمایه‌گذاران غیرفعال",
        "fund_ticker_or_isin": "نماد یا ISIN صندوق:",
        "etf_ticker_or_isin": "نماد یا ISIN ETF:",
        "fund_a": "صندوق A:",
        "fund_b": "صندوق B:",
        "etf_a": "ETF A:",
        "etf_b": "ETF B:",
        "strong_buy": "خرید قوی",
        "buy": "خرید",
        "hold": "نگهداری",
        "caution": "احتیاط",
        "avoid": "اجتناب",
        "language": "زبان",
        "about": "درباره",
        "version": "نسخه",
        "license": "مجوز",
        "developed_by": "توسعه‌دهنده",
        "contact": "تماس",
    },
}


# ---------------------------------------------------------------------------
# Persistent storage
# ---------------------------------------------------------------------------

def _xdg_config_home() -> Path:
    if os.environ.get("XDG_CONFIG_HOME"):
        return Path(os.environ["XDG_CONFIG_HOME"]) / "lynx"
    return Path.home() / ".config" / "lynx"


def language_storage_path() -> Path:
    return _xdg_config_home() / "language.json"


def _load_persisted_language() -> Optional[str]:
    path = language_storage_path()
    try:
        if path.exists():
            return str(json.loads(path.read_text(encoding="utf-8")).get("language") or "")
    except (json.JSONDecodeError, OSError):
        return None
    return None


def _persist_language(code: str) -> None:
    try:
        path = language_storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"language": code}), encoding="utf-8")
    except OSError:
        # Best-effort persistence — if the home dir isn't writable just
        # keep the in-memory choice.
        pass


# ---------------------------------------------------------------------------
# Module state
# ---------------------------------------------------------------------------

def _normalise(code: Optional[str]) -> str:
    if not code:
        return DEFAULT_LANGUAGE
    code = code.strip().lower()
    # Tolerate common spellings: "en" / "en-US" / "english" → "us".
    aliases = {
        "en": "us",
        "english": "us",
        "en-us": "us",
        "en_us": "us",
        "spanish": "es",
        "español": "es",
        "italian": "it",
        "italiano": "it",
        "german": "de",
        "deutsch": "de",
        "french": "fr",
        "français": "fr",
        "francais": "fr",
        "persian": "fa",
        "farsi": "fa",
    }
    code = aliases.get(code, code)
    return code if code in TRANSLATIONS else DEFAULT_LANGUAGE


_current_language: str = _normalise(
    os.environ.get("LYNX_LANG") or _load_persisted_language() or DEFAULT_LANGUAGE
)


def current_language() -> str:
    """Return the active language code (e.g. ``"us"``)."""
    return _current_language


def set_language(code: str, *, persist: bool = True) -> str:
    """Switch the active language. Persists by default. Returns the new code."""
    global _current_language
    _current_language = _normalise(code)
    if persist:
        _persist_language(_current_language)
    return _current_language


def cycle_language(*, persist: bool = True) -> str:
    """Advance to the next supported language (round-robin)."""
    try:
        idx = SUPPORTED_LANGUAGES.index(_current_language)
    except ValueError:
        idx = -1
    new = SUPPORTED_LANGUAGES[(idx + 1) % len(SUPPORTED_LANGUAGES)]
    return set_language(new, persist=persist)


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

def t(key: str, *, lang: Optional[str] = None, default: Optional[str] = None) -> str:
    """Translate *key* into the active (or specified) language.

    Falls back to the US text when the key isn't in the chosen
    language's table, and to *default* (or the key itself) when it
    isn't in the US table either.
    """
    code = _normalise(lang) if lang else _current_language
    table = TRANSLATIONS.get(code, {})
    if key in table:
        return table[key]
    fallback = TRANSLATIONS.get(DEFAULT_LANGUAGE, {})
    if key in fallback:
        return fallback[key]
    return default if default is not None else key


# Short alias used in tight loops / GUIs.
tr = t


# ---------------------------------------------------------------------------
# argparse helper
# ---------------------------------------------------------------------------

def add_language_argument(parser, *, dest: str = "language") -> None:
    """Add a ``--language LANG`` flag to *parser*.

    Accepts both the stable code (``us``, ``es``, ``it``, ``de``,
    ``fr``, ``fa``) and the full English / native names. Defaults to
    the persisted choice (or English if none).
    """
    choices = (
        list(SUPPORTED_LANGUAGES)
        + ["en", "english", "spanish", "italian", "german",
           "french", "persian", "farsi"]
    )
    parser.add_argument(
        "--language",
        dest=dest,
        choices=choices,
        metavar="LANG",
        help=(
            "UI language: us / es / it / de / fr / fa "
            "(default: persisted choice, or English)."
        ),
    )


def apply_args(args, *, dest: str = "language") -> None:
    """Honour ``--language`` if it was supplied on the CLI."""
    val = getattr(args, dest, None)
    if val:
        # CLI flag overrides for this run, but doesn't auto-persist
        # (we don't want a one-off --language=es to silently rewrite
        # the user's saved default).
        set_language(val, persist=False)


# ---------------------------------------------------------------------------
# Helpers exposed for the GUI / TUI corner button
# ---------------------------------------------------------------------------

def language_code_label(code: Optional[str] = None) -> str:
    """Return the short 2-character label shown on the corner button."""
    code = _normalise(code) if code else _current_language
    return LANG_LABELS.get(code, code.upper())


def language_full_name(code: Optional[str] = None) -> str:
    code = _normalise(code) if code else _current_language
    return LANG_FULL_NAMES.get(code, code.upper())


def supported_language_options() -> Iterable[tuple[str, str]]:
    """``(code, full-name)`` tuples in display order."""
    for code in SUPPORTED_LANGUAGES:
        yield code, LANG_FULL_NAMES.get(code, code)
