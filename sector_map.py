"""
sector_map.py
─────────────
Hardcoded sector data for ~300 common NSE tickers so the /api/sector
endpoint never has to hit yfinance for well-known stocks.

Usage
-----
from sector_map import get_sector          # drop-in for yfinance lookup

The public API is intentionally identical to what app.py already does:
    sector_str = get_sector(ticker)        # e.g. "Financial Services"
"""

from __future__ import annotations

# ── Hardcoded master map ───────────────────────────────────────────────────────
# Key   : ticker exactly as used in the app  (suffix .NS included)
# Value : sector string (matches yfinance / Yahoo Finance sector labels)

SECTOR_MAP: dict[str, str] = {
    #  Energy 
    "RELIANCE.NS":    "Energy",
    "ONGC.NS":        "Energy",
    "BPCL.NS":        "Energy",
    "HINDPETRO.NS":   "Energy",
    "IOC.NS":         "Energy",
    "GAIL.NS":        "Energy",
    "PETRONET.NS":    "Energy",
    "ATGL.NS":        "Energy",
    "CONFIPET.NS":    "Energy",
    "SPLPETRO.NS":    "Energy",
    "CHENNPETRO.NS":  "Energy",
    "GUJGASLTD.NS":   "Energy",
    "IGL.NS":         "Energy",
    "MGL.NS":         "Energy",
    "NTPC.NS":        "Energy",
    "NTPCGREEN.NS":   "Energy",
    "TATAPOWER.NS":   "Energy",
    "JSWENERGY.NS":   "Energy",
    "TORNTPOWER.NS":  "Energy",
    "NHPC.NS":        "Energy",
    "SJVN.NS":        "Energy",
    "POWERGRID.NS":   "Energy",
    "PTC.NS":         "Energy",
    "IREDA.NS":       "Energy",
    "RECLTD.NS":      "Energy",
    "PFC.NS":         "Energy",
    "SUZLON.NS":      "Energy",
    "WAAREEENER.NS":  "Energy",
    "ACMESOLAR.NS":   "Energy",
    "KPIGREEN.NS":    "Energy",
    "SOLEX.NS":       "Energy",
    "VIKRAMSOLR.NS":  "Energy",
    "WEBELSOLAR.NS":  "Energy",
    "EMMVEE.NS":      "Energy",
    "UTLSOLAR.NS":    "Energy",
    "SERVOTECH.NS":   "Energy",
    "QPOWER.NS":      "Energy",
    "ATHERENERG.NS":  "Energy",
    "PREMIERENE.NS":  "Energy",
    "NLCINDIA.NS":    "Energy",
    "SARDAEN.NS":     "Energy",
    "NAVA.NS":        "Energy",

    #  Financial Services 
    "HDFCBANK.NS":    "Financial Services",
    "ICICIBANK.NS":   "Financial Services",
    "KOTAKBANK.NS":   "Financial Services",
    "SBIN.NS":        "Financial Services",
    "AXISBANK.NS":    "Financial Services",
    "INDUSINDBK.NS":  "Financial Services",
    "FEDERALBNK.NS":  "Financial Services",
    "IDFCFIRSTB.NS":  "Financial Services",
    "RBLBANK.NS":     "Financial Services",
    "DCBBANK.NS":     "Financial Services",
    "KTKBANK.NS":     "Financial Services",
    "INDIANB.NS":     "Financial Services",
    "BANKBARODA.NS":  "Financial Services",
    "CANBK.NS":       "Financial Services",
    "PNB.NS":         "Financial Services",
    "UNIONBANK.NS":   "Financial Services",
    "IOB.NS":         "Financial Services",
    "MAHABANK.NS":    "Financial Services",
    "JSFB.NS":        "Financial Services",
    "BAJFINANCE.NS":  "Financial Services",
    "BAJAJFINSV.NS":  "Financial Services",
    "CHOLAFIN.NS":    "Financial Services",
    "SHRIRAMFIN.NS":  "Financial Services",
    "MBAPL.NS":       "Financial Services",
    "ARMANFIN.NS":    "Financial Services",
    "SGFIN.NS":       "Financial Services",
    "PAISALO.NS":     "Financial Services",
    "CGCL.NS":        "Financial Services",
    "FEDFINA.NS":     "Financial Services",
    "JMFINANCIL.NS":  "Financial Services",
    "LTF.NS":         "Financial Services",
    "CANFINHOME.NS":  "Financial Services",
    "PNBHOUSING.NS":  "Financial Services",
    "INDIASHLTR.NS":  "Financial Services",
    "AADHARHFC.NS":   "Financial Services",
    "LICI.NS":        "Financial Services",
    "STARHEALTH.NS":  "Financial Services",
    "RELIGARE.NS":    "Financial Services",
    "ANGELONE.NS":    "Financial Services",
    "BSE.NS":         "Financial Services",
    "KFINTECH.NS":    "Financial Services",
    "IEX.NS":         "Financial Services",
    "GROWW.NS":       "Financial Services",
    "ABSLAMC.NS":     "Financial Services",
    "CRAMC.NS":       "Financial Services",

    #  Information Technology 
    "TCS.NS":         "Technology",
    "INFY.NS":        "Technology",
    "HCLTECH.NS":     "Technology",
    "WIPRO.NS":       "Technology",
    "TECHM.NS":       "Technology",
    "PERSISTENT.NS":  "Technology",
    "HAPPSTMNDS.NS":  "Technology",
    "NAUKRI.NS":      "Technology",
    "COFORGE.NS":     "Technology",
    "MPSLTD.NS":      "Technology",
    "DATAMATICS.NS":  "Technology",
    "NINSYS.NS":      "Technology",
    "AXISCADES.NS":   "Technology",
    "TEJASNET.NS":    "Technology",
    "HFCL.NS":        "Technology",
    "DLINKINDIA.NS":  "Technology",
    "SYRMA.NS":       "Technology",
    "DIXON.NS":       "Technology",
    "IXIGO.NS":       "Technology",
    "PAYTM.NS":       "Technology",
    "BLACKBUCK.NS":   "Technology",
    "FIRSTCRY.NS":    "Technology",
    "MEESHO.NS":      "Technology",

    #  Consumer Defensive 
    "HINDUNILVR.NS":  "Consumer Defensive",
    "NESTLEIND.NS":   "Consumer Defensive",
    "BRITANNIA.NS":   "Consumer Defensive",
    "DABUR.NS":       "Consumer Defensive",
    "MARICO.NS":      "Consumer Defensive",
    "COLPAL.NS":      "Consumer Defensive",
    "GODREJCP.NS":    "Consumer Defensive",
    "ITC.NS":         "Consumer Defensive",
    "VBL.NS":         "Consumer Defensive",
    "UBL.NS":         "Consumer Defensive",
    "GMBREW.NS":      "Consumer Defensive",
    "BIKAJI.NS":      "Consumer Defensive",
    "CCL.NS":         "Consumer Defensive",
    "BAJAJCON.NS":    "Consumer Defensive",
    "ZYDUSWELL.NS":   "Consumer Defensive",
    "HONASA.NS":      "Consumer Defensive",

    #  Consumer Cyclical 
    "MARUTI.NS":      "Consumer Cyclical",
    "TATAMOTORS.NS":  "Consumer Cyclical",
    "M&M.NS":         "Consumer Cyclical",
    "EICHERMOT.NS":   "Consumer Cyclical",
    "HEROMOTOCO.NS":  "Consumer Cyclical",
    "BAJAJHCARE.NS":  "Consumer Cyclical",
    "TITAN.NS":       "Consumer Cyclical",
    "TRENT.NS":       "Consumer Cyclical",
    "DMART.NS":       "Consumer Cyclical",
    "PAGEIND.NS":     "Consumer Cyclical",
    "LUXIND.NS":      "Consumer Cyclical",
    "WHIRLPOOL.NS":   "Consumer Cyclical",
    "CROMPTON.NS":    "Consumer Cyclical",
    "VOLTAS.NS":      "Consumer Cyclical",
    "BLUESTARCO.NS":  "Consumer Cyclical",
    "HAVELLS.NS":     "Consumer Cyclical",
    "VGUARD.NS":      "Consumer Cyclical",
    "OBEROIRLTY.NS":  "Consumer Cyclical",
    "STYLEBAAZA.NS":  "Consumer Cyclical",
    "BLUESTONE.NS":   "Consumer Cyclical",
    "DOMS.NS":        "Consumer Cyclical",
    "MEDPLUS.NS":     "Consumer Cyclical",
    "ENTERO.NS":      "Consumer Cyclical",

    #  Healthcare 
    "SUNPHARMA.NS":   "Healthcare",
    "DRREDDY.NS":     "Healthcare",
    "CIPLA.NS":       "Healthcare",
    "DIVISLAB.NS":    "Healthcare",
    "BIOCON.NS":      "Healthcare",
    "LUPIN.NS":       "Healthcare",
    "AUROPHARMA.NS":  "Healthcare",
    "ALKEM.NS":       "Healthcare",
    "TORNTPHARM.NS":  "Healthcare",
    "IPCALAB.NS":     "Healthcare",
    "GLENMARK.NS":    "Healthcare",
    "JUBLPHARMA.NS":  "Healthcare",
    "NATCOPHARM.NS":  "Healthcare",
    "GRANULES.NS":    "Healthcare",
    "LAURUSLABS.NS":  "Healthcare",
    "SOLARA.NS":      "Healthcare",
    "JBCHEPHARM.NS":  "Healthcare",
    "GLAND.NS":       "Healthcare",
    "EMCURE.NS":      "Healthcare",
    "THYROCARE.NS":   "Healthcare",
    "RAINBOW.NS":     "Healthcare",
    "YATHARTH.NS":    "Healthcare",
    "PARKHOSPS.NS":   "Healthcare",
    "ASTERDM.NS":     "Healthcare",
    "APOLLOHOSP.NS":  "Healthcare",
    "INDRAMEDCO.NS":  "Healthcare",
    "INDSWFTLAB.NS":  "Healthcare",
    "SMSPHARMA.NS":   "Healthcare",
    "POLYMED.NS":     "Healthcare",
    "SHILPAMED.NS":   "Healthcare",
    "TATVA.NS":       "Healthcare",
    "ZYDUSLIFE.NS":   "Healthcare",
    "BAJAJHCARE.NS":  "Healthcare",
    "OCCLLTD.NS":     "Healthcare",

    #  Industrials 
    "LT.NS":          "Industrials",
    "SIEMENS.NS":     "Industrials",
    "ABB.NS":         "Industrials",
    "BHEL.NS":        "Industrials",
    "HAL.NS":         "Industrials",
    "BEL.NS":         "Industrials",
    "BDL.NS":         "Industrials",
    "ENGINERSIN.NS":  "Industrials",
    "IRCON.NS":       "Industrials",
    "IRCTC.NS":       "Industrials",
    "IRFC.NS":        "Industrials",
    "RVNL.NS":        "Industrials",
    "RITES.NS":       "Industrials",
    "CONCOR.NS":      "Industrials",
    "DELHIVERY.NS":   "Industrials",
    "BLS.NS":         "Industrials",
    "KEC.NS":         "Industrials",
    "THERMAX.NS":     "Industrials",
    "CUMMINSIND.NS":  "Industrials",
    "ISGEC.NS":       "Industrials",
    "JBMA.NS":        "Industrials",
    "CAPACITE.NS":    "Industrials",
    "CEIGALL.NS":     "Industrials",
    "IRB.NS":         "Industrials",
    "COCHINSHIP.NS":  "Industrials",
    "GESHIP.NS":      "Industrials",
    "MAZDOCK.NS":     "Industrials",
    "SEAMECLTD.NS":   "Industrials",
    "TDPOWERSYS.NS":  "Industrials",
    "POWERINDIA.NS":  "Industrials",
    "SCHNEIDER.NS":   "Industrials",
    "CENTUM.NS":      "Industrials",
    "DATAPATTNS.NS":  "Industrials",
    "MTARTECH.NS":    "Industrials",
    "JNKINDIA.NS":    "Industrials",
    "SKIPPER.NS":     "Industrials",
    "INOXINDIA.NS":   "Industrials",
    "WAAREEINDO.NS":  "Industrials",
    "WAAREERTL.NS":   "Industrials",
    "AEROFLEX.NS":    "Industrials",
    "SANSERA.NS":     "Industrials",
    "GABRIEL.NS":     "Industrials",
    "PRICOLLTD.NS":   "Industrials",
    "LUMAXTECH.NS":   "Industrials",
    "TIINDIA.NS":     "Industrials",
    "MINDACORP.NS":   "Industrials",
    "UNOMINDA.NS":    "Industrials",
    "SONACOMS.NS":    "Industrials",
    "WHEELS.NS":      "Industrials",
    "FIEMIND.NS":     "Industrials",

    #  Basic Materials 
    "TATASTEEL.NS":   "Basic Materials",
    "JSWSTEEL.NS":    "Basic Materials",
    "HINDALCO.NS":    "Basic Materials",
    "SAIL.NS":        "Basic Materials",
    "NMDC.NS":        "Basic Materials",
    "COALINDIA.NS":   "Basic Materials",
    "VEDL.NS":        "Basic Materials",
    "NATIONALUM.NS":  "Basic Materials",
    "MOIL.NS":        "Basic Materials",
    "KIOCL.NS":       "Basic Materials",
    "GMDCLTD.NS":     "Basic Materials",
    "GPIL.NS":        "Basic Materials",
    "ELECTCAST.NS":   "Basic Materials",
    "RATNAMANI.NS":   "Basic Materials",
    "WELCORP.NS":     "Basic Materials",
    "MAHSEAMLES.NS":  "Basic Materials",
    "SCODATUBES.NS":  "Basic Materials",
    "APOLLOPIPE.NS":  "Basic Materials",
    "ASTRAL.NS":      "Basic Materials",
    "SUPREMEIND.NS":  "Basic Materials",
    "POLYCAB.NS":     "Basic Materials",
    "UNIVCABLES.NS":  "Basic Materials",
    "PARACABLES.NS":  "Basic Materials",
    "PRECWIRE.NS":    "Basic Materials",
    "VIDYAWIRES.NS":  "Basic Materials",
    "ASIANPAINT.NS":  "Basic Materials",
    "BERGEPAINT.NS":  "Basic Materials",
    "PIDILITIND.NS":  "Basic Materials",
    "NAVINFLUOR.NS":  "Basic Materials",
    "ALKYLAMINE.NS":  "Basic Materials",
    "BALAMINES.NS":   "Basic Materials",
    "EPIGRAL.NS":     "Basic Materials",
    "NOCIL.NS":       "Basic Materials",
    "IOLCP.NS":       "Basic Materials",
    "GUJALKALI.NS":   "Basic Materials",
    "LINDEINDIA.NS":  "Basic Materials",
    "CARBORUNIV.NS":  "Basic Materials",
    "ULTRACEMCO.NS":  "Basic Materials",
    "SHREECEM.NS":    "Basic Materials",
    "AMBUJACEM.NS":   "Basic Materials",
    "ACC.NS":         "Basic Materials",
    "DALBHARAT.NS":   "Basic Materials",
    "RAMCOCEM.NS":    "Basic Materials",
    "JKCEMENT.NS":    "Basic Materials",
    "MANGLMCEM.NS":   "Basic Materials",
    "CENTURYPLY.NS":  "Basic Materials",
    "GREENPLY.NS":    "Basic Materials",
    "JINDALSTEL.NS":  "Basic Materials",
    "SHYAMMETL.NS":   "Basic Materials",
    "SAMBHV.NS":      "Basic Materials",
    "GPIL.NS":        "Basic Materials",
    "FACT.NS":        "Basic Materials",
    "KSCL.NS":        "Basic Materials",
    "TATVA.NS":       "Basic Materials",
    "POCL.NS":        "Basic Materials",
    "MAYURUNIQ.NS":   "Basic Materials",
    "XPROINDIA.NS":   "Basic Materials",
    "PREMIERPOL.NS":  "Basic Materials",
    "SHAILY.NS":      "Basic Materials",
    "MBAPL.NS":       "Basic Materials",

    #  Real Estate 
    "OBEROIRLTY.NS":  "Real Estate",
    "JUBLINGREA.NS":  "Real Estate",
    "GODAVARIB.NS":   "Real Estate",
    "URBANCO.NS":     "Real Estate",
    "NITCO.NS":       "Real Estate",
    "RIIL.NS":        "Real Estate",

    #  Communication Services 
    "BHARTIARTL.NS":  "Communication Services",
    "BHARTIHEXA.NS":  "Communication Services",
    "SUNTV.NS":       "Communication Services",
    "STAR.NS":        "Communication Services",

    #  Utilities 
    "WABAG.NS":       "Utilities",
    "CEWATER.NS":     "Utilities",

    #  Sugar / Agri 
    "DALMIASUG.NS":   "Consumer Defensive",
    "DHAMPURSUG.NS":  "Consumer Defensive",
    "AVADHSUGAR.NS":  "Consumer Defensive",
    "UTTAMSUGAR.NS":  "Consumer Defensive",
    "UGARSUGAR.NS":   "Consumer Defensive",
    "DWARKESH.NS":    "Consumer Defensive",
    "ANDHRSUGAR.NS":  "Consumer Defensive",
    "DCMSHRIRAM.NS":  "Consumer Defensive",
    "GOKULAGRO.NS":   "Consumer Defensive",
    "PONNIERODE.NS":  "Consumer Defensive",

    #  Auto ancillaries / misc manufacturing 
    "CEATLTD.NS":     "Consumer Cyclical",
    "SCHAEFFLER.NS":  "Industrials",
    "KSB.NS":         "Industrials",
    "KIRLPNU.NS":     "Industrials",
    "EIMCOELECO.NS":  "Industrials",
    "VOLTAMP.NS":     "Industrials",
    "HBLENGINE.NS":   "Industrials",
    "JSWINFRA.NS":    "Industrials",
    "GVT&D.NS":       "Industrials",
    "KPEL.NS":        "Industrials",
    "TARIL.NS":       "Industrials",
    "JAYNECOIND.NS":  "Industrials",
    "DEEPINDS.NS":    "Industrials",
    "ORKLAINDIA.NS":  "Industrials",
    "WABAG.NS":       "Industrials",
    "ISGEC.NS":       "Industrials",
    "NACLIND.NS":     "Basic Materials",
    "PLATIND.NS":     "Basic Materials",
    "MIDWESTLTD.NS":  "Basic Materials",

    #  Specialty / misc 
    "AETHER.NS":      "Basic Materials",
    "GLAND.NS":       "Healthcare",
    "JUBLINGREA.NS":  "Real Estate",
    "JKPAPER.NS":     "Basic Materials",
    "SOUTHWEST.NS":   "Industrials",
    "PNGPL.NS":       "Energy",
    "PNGJL.NS":       "Energy",
    "RUBICON.NS":     "Technology",
    "NPST.NS":        "Technology",
    "SRM.NS":         "Industrials",
    "VTL.NS":         "Industrials",
    "PWL.NS":         "Industrials",
    "BLSE.NS":        "Industrials",
    "EBGNG.NS":       "Industrials",
    "RIIL.NS":        "Industrials",
    "ACI.NS":         "Industrials",
    "AVL.NS":         "Industrials",
    "AIIL.NS":        "Industrials",
    "IGIL.NS":        "Industrials",
    "INDGN.NS":       "Industrials",
    "AKUMS.NS":       "Healthcare",
    "AGIIL.NS":       "Industrials",
    "ACUTAAS.NS":     "Technology",
    "ANUP.NS":        "Industrials",
    "ANURAS.NS":      "Healthcare",
    "APEX.NS":        "Industrials",
    "ARFIN.NS":       "Basic Materials",
    "ARVIND.NS":      "Consumer Cyclical",
    "ALIVUS.NS":      "Healthcare",
    "APARINDS.NS":    "Industrials",
    "AVALON.NS":      "Technology",
    "BAYERCROP.NS":   "Basic Materials",
    "BEPL.NS":        "Basic Materials",
    "BELRISE.NS":     "Consumer Cyclical",
    "BUILDPRO.NS":    "Industrials",
    "CAPACITE.NS":    "Industrials",
    "COHANCE.NS":     "Technology",
    "CUPID.NS":       "Healthcare",
    "DIVGIITTS.NS":   "Industrials",
    "FISCHER.NS":     "Industrials",
    "FORCEMOT.NS":    "Consumer Cyclical",
    "GLOBUSSPR.NS":   "Consumer Cyclical",
    "HSCL.NS":        "Basic Materials",
    "JARO.NS":        "Consumer Cyclical",
    "JAINREC.NS":     "Basic Materials",
    "KECL.NS":        "Industrials",
    "KRN.NS":         "Industrials",
    "KSHINTL.NS":     "Basic Materials",
    "OSWALP.NS":      "Industrials",
    "OSWALPUMPS.NS":  "Industrials",
    "PFOCUS.NS":      "Technology",
    "PRIVISCL.NS":    "Healthcare",
    "SAKAR.NS":       "Basic Materials",
    "SAILIFE.NS":     "Consumer Defensive",
    "SGMART.NS":      "Consumer Cyclical",
    "SHRIPISTON.NS":  "Consumer Cyclical",
    "SIRCA.NS":       "Basic Materials",
    "SJS.NS":         "Consumer Cyclical",
    "SPORTKING.NS":   "Consumer Cyclical",
    "TVSELECT.NS":    "Industrials",
    "TI.NS":          "Industrials",
    "VENUSREM.NS":    "Healthcare",
    "VINCOFE.NS":     "Basic Materials",
    "JAINREC.NS":     "Basic Materials",
    "BOHRAIND.NS":    "Industrials",
    "ATLANTAELE.NS":  "Industrials",
    "ADANIGREEN.NS":  "Energy",
    "ADANIENT.NS":    "Industrials",
    "ADANIPORTS.NS":  "Industrials",
    "ADANIPOWER.NS":  "Energy",
    "CERA.NS":        "Consumer Cyclical",
    "GRASIM.NS":      "Basic Materials",
    "BOHRAIND.NS":    "Industrials",
    "BOHRAIND.NS":    "Industrials",
    "JSWINFRA.NS":    "Industrials",
    "ETERNAL.NS":     "Consumer Cyclical",
    "BOHRAIND.NS":    "Industrials",
}

# ── Runtime cache (populated by live yfinance lookups for unknown tickers) ────
_live_cache: dict[str, str] = {}


def get_sector(ticker: str) -> str:
    """
    Return the sector for *ticker*.

    Resolution order:
        1. Hardcoded SECTOR_MAP  — instant, no network
        2. _live_cache           — previous yfinance hit this session
        3. yfinance live lookup  — network call, result stored in _live_cache
        4. Fallback: "Other"
    """
    # Normalise: always upper-case, ensure .NS suffix present
    t = ticker.strip().upper()
    if "." not in t:
        t += ".NS"

    # 1. Hardcoded map
    if t in SECTOR_MAP:
        return SECTOR_MAP[t]

    # 2. Session cache
    if t in _live_cache:
        return _live_cache[t]

    # 3. Live yfinance lookup
    try:
        import yfinance as yf
        info = yf.Ticker(t).info
        sector = info.get("sector") or "Other"
    except Exception:
        sector = "Other"

    # 4. Cache result (even "Other") to avoid repeat network calls
    _live_cache[t] = sector
    return sector


def warm_cache(tickers: list[str]) -> None:
    """
    Pre-populate _live_cache for a list of tickers not in SECTOR_MAP.
    Call this on app startup or after the user adds multiple tickers.
    """
    unknown = [
        t.strip().upper() if "." in t else t.strip().upper() + ".NS"
        for t in tickers
        if (t.strip().upper() if "." in t else t.strip().upper() + ".NS") not in SECTOR_MAP
        and (t.strip().upper() if "." in t else t.strip().upper() + ".NS") not in _live_cache
    ]
    for t in unknown:
        get_sector(t)   # populates _live_cache as a side-effect